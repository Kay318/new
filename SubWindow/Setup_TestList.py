import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))
from Helper import *
from Log import LogManager
from DataBase import DB as db
from Settings import Setup as sp
from SubWindow.LoadingScreen import LoadingScreen

class Setup_TestList(QDialog):
    signal = pyqtSignal(list, list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fieldList = parent.fieldList
        # self.db = DBManager()
        self.sp = sp.Settings()
        self.setupUI_TestList()

    @AutomationFunctionDecorator
    def setupUI_TestList(self):
        self.setWindowTitle("평가목록 설정")

        self.setWindowFlags(
        Qt.Window |
        Qt.CustomizeWindowHint |
        Qt.WindowCloseButtonHint |
        Qt.WindowStaysOnTopHint
        )

        # 전체 화면 배치
        self.verticalLayout = QVBoxLayout(self)

        # Setup.ini 파일에 데이터를 창에 표시
        testList, _ = self.sp.read_setup(table = "Test_List")
        check_first = True

        for i in range(8):
            globals()[f'horizontalLayout{i}'] = QHBoxLayout()

            globals()[f'label{i}'] = QLabel()
            globals()[f'label{i}'].setText(f"{i+1}")
            globals()[f'horizontalLayout{i}'].addWidget(globals()[f'label{i}'])

            globals()[f'lineEdit{i}'] = QLineEdit()
            globals()[f'horizontalLayout{i}'].addWidget(globals()[f'lineEdit{i}'])
            self.verticalLayout.addLayout(globals()[f'horizontalLayout{i}'])
            try:
                globals()[f'lineEdit{i}'].setText(testList[i])
            except:
                pass

            # 포커스 설정: 빈칸 혹은 마지막칸
            if (globals()[f'lineEdit{i}'].text() == "" or i==7) and check_first:
                globals()[f'lineEdit{i}'].setFocus()
                check_first = False

        # [확인], [취소] 버튼
        self.ok_horizontalLayout = QHBoxLayout()
        self.ok_horizontalLayout.setAlignment(Qt.AlignRight)
        
        self.ok_Button = QPushButton("확인", self)
        self.ok_horizontalLayout.addWidget(self.ok_Button)
        self.cancel_Button = QPushButton("취소", self)
        self.ok_horizontalLayout.addWidget(self.cancel_Button)
        self.verticalLayout.addLayout(self.ok_horizontalLayout)

        # 버튼 이벤트 함수
        self.tl_set_slot()

    @AutomationFunctionDecorator
    def tl_set_slot(self):
        self.ok_Button.clicked.connect(self.ok_Button_clicked)
        self.cancel_Button.clicked.connect(self.close)

    @AutomationFunctionDecorator
    def ok_Button_clicked(self, litter):
        LogManager.HLOG.info("평가 목록 설정 팝업 확인 버튼 선택")
        testList = []

        # 중복 체크
        for i in range(8):
            if globals()[f'lineEdit{i}'].text() != "":
                if any(elem in list(globals()[f'lineEdit{i}'].text()) for elem in ["%", "'", "{", "}", ":", ";"]):
                    QMessageBox.warning(self, '주의', '["%", "\'", "\{", "\}", ":", ";"] 특수문자는 사용할 수 없습니다.')
                    LogManager.HLOG.info(f'평가목록 설정 팝업에서 특수문자 알림 표시')
                    return

                if len(globals()[f'lineEdit{i}'].text()) > 25:
                    QMessageBox.warning(self, '주의', '최대 길이는 25자입니다.')
                    LogManager.HLOG.info(f'평가목록 설정 팝업에서 최대 길이 알림 표시')
                    return

                if globals()[f'lineEdit{i}'].text() not in testList:
                    testList.append(globals()[f'lineEdit{i}'].text())
                else:
                    QMessageBox.warning(self, '주의', '중복 라인이 있습니다.')
                    LogManager.HLOG.info("평가 목록 팝업에서 중복 라인 알림 표시")
                    return

                if globals()[f'lineEdit{i}'].text() in self.fieldList:
                    x = globals()[f'lineEdit{i}'].text()
                    QMessageBox.warning(self, '주의', f'"{x}"는 필드에도 있습니다.')
                    LogManager.HLOG.info(f'평가 목록 팝업과 필드 설정 팝업에서 "{x}" 겹침 알림 표시')
                    return

        newColumns = []
        if self.check_changedData():
            reply = QMessageBox.question(self, '알림', '모든 언어에서 평가 목록이 변경됩니다.\n계속하시겠습니까?',
                                        QMessageBox.Ok | QMessageBox.No, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.loadingScreen =LoadingScreen(self)
                self.startLoading()
                newColumns.append("이미지")
                newColumns = newColumns + testList + self.fieldList
                newColumns.append("버전 정보")
                newColumnsSet = set(newColumns)
                # self.db.c.execute("SELECT name FROM sqlite_master WHERE type='table';")
                # sql_tables = self.db.c.fetchall()
                sql_tables = db.db_select("SELECT name FROM sqlite_master WHERE type='table';")
                sql_tables_list = [table[0] for table in sql_tables]
                for sql_table in sql_tables_list:
                    # self.db.c.execute(f"SELECT * FROM '{sql_table}'")
                    # sql_col_set = set([col_tuple[0] for col_tuple in self.db.c.description])
                    sql_col_set = db.db_tables(f"SELECT * FROM '{sql_table}'")
                    col_intersection = tuple(sql_col_set & newColumnsSet)
                    col_subtraction = tuple(newColumnsSet - set(col_intersection))
                    
                    # 컬럼 편집(BACKUP 테이블 만듬 > 기존 테이블 내용을 BACKUP에 옮김 > BACKUP 테이블명 변경)
                    try:
                        # self.db.c.execute("DROP TABLE BACKUP")
                        db.db_edit("DROP TABLE BACKUP")
                    except:
                        pass
                    
                    query = f"CREATE TABLE 'BACKUP' ("
                    for i, col in enumerate(newColumns):
                        if i != len(newColumns) - 1:
                            query += f"'{col}' TEXT,"
                        else:
                            query += f"'{col}' TEXT)"
                    LogManager.HLOG.info(f"평가결과 저장 query:{query}")

                    # self.db.c.execute(query)
                    db.db_edit(query)

                    query_insert = f"INSERT INTO BACKUP {col_intersection} SELECT "
                    for col in col_intersection:
                        if " " in col:
                            col_noSpace = col.replace(" ","")
                            query_insert += f'"{col}" as "{col_noSpace}",'
                            continue
                        query_insert += f'"{col}",'
                    query_insert = f"{query_insert[:-1]} FROM '{sql_table}'"
                    LogManager.HLOG.info(query_insert)
                    # self.db.c.execute(query_insert)
                    # self.db.dbConn.commit()
                    db.db_edit(query_insert)

                    if col_subtraction != ():
                        query_update = f"UPDATE BACKUP SET "
                        for col in col_subtraction:
                            query_update += f"'{col}' = '',"
                        query_update = query_update[:-1]
                        LogManager.HLOG.info(query_update)
                        # self.db.c.execute(query_update)
                        # self.db.dbConn.commit()
                        db.db_edit(query_update)

                #     self.db.c.execute(f"DROP TABLE '{sql_table}'")
                    # self.db.c.execute(f"ALTER TABLE BACKUP RENAME TO '{sql_table}'")
                    db.db_edit(f"DROP TABLE '{sql_table}'")
                    db.db_edit(f"ALTER TABLE BACKUP RENAME TO '{sql_table}'")
                    QApplication.processEvents()
                # self.db.close()
                
            else:
                return
        else:
            self.signal.emit([], [])
            self.destroy()

        self.sp.config["Test_List"] = {}
        for i in range(8):
            if globals()[f'lineEdit{i}'].text() != "":
                self.sp.write_setup(table = "Test_List", 
                                    count=i, 
                                    val=globals()[f'lineEdit{i}'].text(),
                                    val2=None)
                LogManager.HLOG.info(f"{i+1}:평가 목록 팝업에 {globals()[f'lineEdit{i}'].text()} 추가")
        if testList == []:
            testList = ["OK"]
            self.sp.clear_table("Test_List")
        self.signal.emit(testList, newColumns)
        self.destroy()
        # QCoreApplication.instance().quit()

    def check_changedData(self):
        """변경사항이 있는지 체크하는 함수

        Returns:
            _type_: 변경사항이 있으면 True, 없으면 False
        """
        setupList, _ = self.sp.read_setup("Test_List")
        lineList = [globals()[f'lineEdit{i}'].text() for i in range(8) if globals()[f'lineEdit{i}'].text() != ""]
        
        if setupList != lineList:
            return True
        else:
            return False

    def startLoading(self):
        self.setEnabled(False)
        self.loadingScreen.startAnimation()
        
    @AutomationFunctionDecorator
    def closeEvent(self, event) -> None:
        LogManager.HLOG.info("평가 목록 설정 팝업 취소 버튼 선택")

        if self.check_changedData():
            reply = QMessageBox.question(self, '알림', '변경사항이 있습니다.\n취소하시겠습니까?',
                                    QMessageBox.Ok | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Ok:
                LogManager.HLOG.info("필드 설정 팝업 > 취소 > 변경사항 알림에서 예 선택")
                event.accept()
                self.signal.emit([], [])
            else:
                LogManager.HLOG.info("필드 설정 팝업 > 취소 > 변경사항 알림에서 취소 선택")
                event.ignore()
        else:
            self.signal.emit([], [])
            self.destroy()

                
    @AutomationFunctionDecorator
    def keyPressEvent(self, a0: QKeyEvent) -> None:
        
        KEY_ENTER = 16777220
        KEY_SUB_ENTER = 16777221
        KEY_CLOSE = 16777216

        if a0.key() == KEY_ENTER or a0.key() == KEY_SUB_ENTER:
            self.ok_Button_clicked(None)
        elif a0.key() == KEY_CLOSE:
            self.close()

if __name__ == "__main__":
    LogManager.Init()
    app = QApplication(sys.argv)
    ui = Setup_TestList()
    ui.show()
    sys.exit(app.exec_())