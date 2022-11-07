import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))
from Helper import *
from Log import LogManager
from Database.DB import DBManager
from Settings import Setup as sp

class Setup_TestList(QDialog, DBManager):
    signal = pyqtSignal(list, list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fieldList = parent.fieldList
        self.sp = sp.Settings()
        self.setupUI_TestList()

    @AutomationFunctionDecorator
    def setupUI_TestList(self):
        self.setWindowTitle("평가목록 설정")

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

        if self.check_changedData():
            reply = QMessageBox.question(self, '알림', '모든 언어에서 평가 목록이 변경됩니다.\n계속하시겠습니까?',
                                        QMessageBox.Ok | QMessageBox.No, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                newColumns = []
                newColumns.append("이미지")
                newColumns = newColumns + testList + self.fieldList
                newColumns.append("버전정보")
                newColumnsSet = set(newColumns)
                self.c.execute("SELECT name FROM sqlite_master WHERE type='table';")
                sql_tables = self.c.fetchall()
                sql_tables_list = [table[0] for table in sql_tables]
                for sql_table in sql_tables_list:
                    self.c.execute(f"SELECT * FROM ({sql_table})")
                    sql_col_set = set([col_tuple[0] for col_tuple in self.c.description])
                    col_intersection = tuple(sql_col_set & newColumnsSet)
                    
                    # 컬럼 편집(BACKUP 테이블 만듬 > 기존 테이블 내용을 BACKUP에 옮김 > BACKUP 테이블명 변경)
                    try:
                        self.c.execute("DROP TABLE BACKUP")
                    except:
                        pass
                    
                    query = f"CREATE TABLE 'BACKUP' ("
                    for i, col in enumerate(newColumns):
                        if i != len(newColumns) - 1:
                            query += f"'{col}' TEXT,"
                        else:
                            query += f"'{col}' TEXT)"
                    LogManager.HLOG.info(f"평가결과 저장 query:{query}")
        
                    self.c.execute(query)
                    query_insert = f"INSERT INTO BACKUP {col_intersection} SELECT "
                    for col in col_intersection:
                        if " " in col:
                            col_noSpace = col.replace(" ","")
                            query_insert += f'"{col}" as "{col_noSpace}",'
                            continue
                        query_insert += f'"{col}",'
                    query_insert = f"{query_insert[:-1]} FROM {sql_table}"
                    LogManager.HLOG.info(query_insert)
                    self.c.execute(query_insert)
                    self.dbConn.commit()
                    self.c.execute(f"DROP TABLE {sql_table}")
                    self.c.execute(f"ALTER TABLE BACKUP RENAME TO {sql_table}")
                    
            else:
                return
        else:
            return

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