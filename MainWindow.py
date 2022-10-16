# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'untitled.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from functools import partial
import traceback
from PIL import Image
import sys
import os
from pathlib import Path
from SubWindow.ImageView import ImageViewer
from SubWindow.Setup_Language import Setup_Language
from SubWindow.Setup_Field import Setup_Field
from SubWindow.Setup_TestList import Setup_TestList
from Helper import *
sys.path.append(str(Path(__file__).parents[1]))
from Database.DB import DBManager
from Log import LogManager
from Settings import Setup as sp

class MainWindow(QMainWindow, DBManager):
    
    def __init__(self):
        super().__init__()
        self.field_lineEdit = []                 # 모든 필드
        self.all_RadioList = []                  # 모든 라디오 버튼
        self.pass_RadioList = []                 # 모든 pass 버튼
        self.fail_RadioList = []                 # 모든 fail 버튼
        self.nt_RadioList = []                   # 모든 N/T 버튼
        self.na_RadioList = []                   # 모든 N/A 버튼
        self.nl_RadioList = []                   # 모든 NULL 버튼
        self.imgList = []                        # 선택된 경로의 이미지 리스트
        self.idx = ""                            # 좌측 이미지 버튼 index
        self.button = ""                         # 좌측 이미지 버튼
        self.img_dir = ""                        # 이미지 경로
        self.setupList = []                      # 필드와 평가결과에 들어가는 모든 항목
        self.result = {}                         # 매 이미지에 대한 결과값 저장
        self.clicked_lang = ""                   # 선택된 언어
        self.pre_lang = ""                       # 그전에 선택된 언어
        self.pre_subMenu = None                  # 메뉴바에서 그전에 선택된 언어 subMenu
        self.nextImg_bool = True                 # 다음 이미지로 넘어갈지 판단
        # self.loadingThread = LoadingThread()
        # self.loadingThread.loading_singnal.connect(self.start_loading)
        self.sp = sp.Settings()
        self.setupUi()
        
    @AutomationFunctionDecorator
    def setupUi(self):
        
        widget = QWidget()

        # 해상도 받아옴
        screen = QDesktopWidget().screenGeometry()

        # 해상도에 따라 창 크기 설정
        main_width = round(screen.width() * 0.7)                   # 메인창 넓이
        main_height = round(screen.height() * 0.7)                 # 메인창 높이
        main_left = round((screen.width() - main_width) / 2)       # 메인창 x좌표
        main_top = round((screen.height() - main_height) / 2)      # 메인창 y좌표
        img_scrollArea_width = round(main_width / 15)              # 좌측 이미지 스크롤 영역 넓이
        left_right_imgBtn_width = round(main_width / 20)           # [<], [>] 버튼 넓이
        allButton_spacing = 10                              # all 버튼 간격
        self.bottom_groupbox_fixedHeight = 210                   # bottom 영역 높이값

        if main_width > 1344:
            main_width = 1344
        if main_height > 756:
            main_height = 756

        self.setMinimumSize(main_width, main_height)
        self.setGeometry(main_left, main_top, main_width, main_height)
        self.setWindowTitle("다국어 자동화")

        # 전체 화면 배치
        horizontalLayout = QHBoxLayout(widget)
        self.setCentralWidget(widget)

        # 좌측 이미지 리스트
        img_scrollArea = QScrollArea()
        img_scrollArea.setWidgetResizable(True)
        img_scrollArea.setFixedWidth(img_scrollArea_width)
    
        img_scrollAreaWidgetContents = QWidget()
        self.img_VBoxLayout = QVBoxLayout(img_scrollAreaWidgetContents)
        self.img_VBoxLayout.setAlignment(Qt.AlignTop)

        img_scrollArea.setWidget(img_scrollAreaWidgetContents)
        horizontalLayout.addWidget(img_scrollArea)

        # 우측 큰 이미지
        right_VBoxLayout = QVBoxLayout()
        img_hbox = QHBoxLayout(self)

        self.left_imgBtn = QPushButton("<")
        self.left_imgBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.left_imgBtn.setFixedWidth(left_right_imgBtn_width)
        self.left_imgBtn.setShortcut('Alt+left')
        self.left_imgBtn.clicked.connect(partial(self.btn_onClicked))
        self.left_imgBtn.setEnabled(False)

        self.right_imgBtn = QPushButton(">")
        self.right_imgBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_imgBtn.setFixedWidth(left_right_imgBtn_width)
        self.right_imgBtn.setShortcut('Alt+right')
        self.right_imgBtn.clicked.connect(partial(self.btn_onClicked))
        self.right_imgBtn.setEnabled(False)

        self.img_Label = QLabel()
        self.img_Label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.img_Label.setStyleSheet("color: gray;"
                                "border-style: solid;"
                                "border-width: 1px;"
                                "border-color: #747474;"
                                "border-radius: 1px")

        img_hbox.addWidget(self.left_imgBtn)
        img_hbox.addWidget(self.img_Label)
        img_hbox.addWidget(self.right_imgBtn)
        right_VBoxLayout.addLayout(img_hbox)

        # 필드 세팅
        self.field_gridLayout = QGridLayout()
        self.fieldList, _ = self.sp.read_setup(table = "Field")
        self.set_field_gridLayout()
        right_VBoxLayout.addLayout(self.field_gridLayout)

        # 평가 목록, all pass, fail      
        self.bottom_gridLayout = QGridLayout()
        self.testList, _ = self.sp.read_setup(table = "Test_List")
        self.set_testList_hboxLayout()
        
        # ALL PASS, ALL FAIL, ALL N/T, ALL N/A
        all_groupbox = QGroupBox("ALL")
        all_groupbox.setFixedHeight(self.bottom_groupbox_fixedHeight)
                
        testAll_VBoxLayout = QVBoxLayout()
        self.allPass_RadioButton = QPushButton("ALL PASS")
        self.allPass_RadioButton.setStyleSheet("background-color: rgb(62,74,193); color:white;")
        self.allPass_RadioButton.setEnabled(False)
        self.allFail_RadioButton = QPushButton("ALL FAIL")
        self.allFail_RadioButton.setStyleSheet("background-color: rgb(211,44,98); color:white;")
        self.allFail_RadioButton.setEnabled(False)
        self.allNT_RadioButton = QPushButton("ALL N/T")
        self.allNT_RadioButton.setStyleSheet("background-color: rgb(56,199,81); color:white;")
        self.allNT_RadioButton.setEnabled(False)
        self.allNA_RadioButton = QPushButton("ALL N/A")
        self.allNA_RadioButton.setStyleSheet("background-color: rgb(64,128,128); color:white;")
        self.allNA_RadioButton.setEnabled(False)
        self.allNull_RadioButton = QPushButton("ALL NULL")
        self.allNull_RadioButton.setEnabled(False)
        testAll_VBoxLayout.addWidget(self.allPass_RadioButton)
        testAll_VBoxLayout.addSpacing(allButton_spacing)
        testAll_VBoxLayout.addWidget(self.allFail_RadioButton)
        testAll_VBoxLayout.addSpacing(allButton_spacing)
        testAll_VBoxLayout.addWidget(self.allNT_RadioButton)
        testAll_VBoxLayout.addSpacing(allButton_spacing)
        testAll_VBoxLayout.addWidget(self.allNA_RadioButton)
        testAll_VBoxLayout.addSpacing(allButton_spacing)
        testAll_VBoxLayout.addWidget(self.allNull_RadioButton)
        testAll_VBoxLayout.setAlignment(Qt.AlignCenter)

        self.allPass_RadioButton.clicked.connect(self.__allPass_clicked)
        self.allFail_RadioButton.clicked.connect(self.__allFail_clicked)
        self.allNT_RadioButton.clicked.connect(self.__allNT_clicked)
        self.allNA_RadioButton.clicked.connect(self.__allNA_clicked)
        self.allNull_RadioButton.clicked.connect(self.__allNull_clicked)
        all_groupbox.setLayout(testAll_VBoxLayout)
        self.bottom_gridLayout.addWidget(all_groupbox, 0, 4, 1, 1)

        # 버전 정보
        version_groupbox = QGroupBox("버전 정보")
        version_groupbox.setFixedHeight(self.bottom_groupbox_fixedHeight)
        version_VBoxLayout = QVBoxLayout()
        self.version_textEdit = QTextEdit()
        self.version_textEdit.setEnabled(False)
        version_VBoxLayout.addWidget(self.version_textEdit)
        version_groupbox.setLayout(version_VBoxLayout)
        self.bottom_gridLayout.addWidget(version_groupbox, 0, 5, 1, 3)

        # 진행 상황
        result_groupbox = QGroupBox("진행 상황")
        result_groupbox.setFixedHeight(self.bottom_groupbox_fixedHeight)
        result_Layout = QVBoxLayout()
        self.null_lbl = QLabel("미평가:")
        self.pass_lbl = QLabel("PASS:")
        self.fail_lbl = QLabel("FAIL:")
        self.nt_lbl = QLabel("N/T:")
        self.na_lbl = QLabel("N/A:")
        result_Layout.addWidget(self.null_lbl)
        result_Layout.addWidget(self.pass_lbl)
        result_Layout.addWidget(self.fail_lbl)
        result_Layout.addWidget(self.nt_lbl)
        result_Layout.addWidget(self.na_lbl)
        result_groupbox.setLayout(result_Layout)

        self.bottom_gridLayout.addWidget(result_groupbox, 0, 8, 1, 1)

        right_VBoxLayout.addLayout(self.bottom_gridLayout)
        horizontalLayout.addLayout(right_VBoxLayout)

        # 메뉴바
        self.menubar = self.menuBar()
        self.menu = self.menubar.addMenu("&Menu")
        self.menuOpen = self.menu.addMenu("Open")
        langList, langPath = self.sp.read_setup(table = "Language")
        for lang, path in zip(langList, langPath):
            subMenu = QAction(lang, self)
            self.menuOpen.addAction(subMenu)
            subMenu.setCheckable(True)
            subMenu.triggered.connect(partial(self.show_imgList, lang, path, subMenu))
            
        self.actionSave = QAction("Save", self)
        self.actionSave.setShortcut("Ctrl+S")
        self.actionCreateExcel = QAction("Create Excel", self)
        self.actionClose = QAction("Close", self)
        self.menu.addMenu(self.menuOpen)
        self.menu.addAction(self.actionSave)
        self.menu.addAction(self.actionCreateExcel)
        self.menu.addAction(self.actionClose)
        self.actionSave.triggered.connect(self.save_result)
        self.actionSave.setEnabled(False)

        self.setup = self.menubar.addMenu("&Setup")
        self.actionLanguage = QAction("Language", self)
        self.actionField = QAction("Field", self)
        self.actionTest_List = QAction("Test List", self)
        self.actionExcel_Setting = QAction("Excel Setting", self)
        self.actionLanguage.setShortcut("Ctrl+1")
        self.actionField.setShortcut("Ctrl+2")
        self.actionTest_List.setShortcut("Ctrl+3")
        self.actionExcel_Setting.setShortcut("Ctrl+4")
        self.setup.addAction(self.actionLanguage)
        self.setup.addAction(self.actionField)
        self.setup.addAction(self.actionTest_List)
        self.setup.addAction(self.actionExcel_Setting)
        self.actionLanguage.triggered.connect(self.show_setup_Language)
        self.actionField.triggered.connect(self.show_setup_Field)
        self.actionTest_List.triggered.connect(self.show_setup_TestList)
        
        # 상태바
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        self.statusbar_label = QLabel()
        statusbar.addPermanentWidget(self.statusbar_label)

    @AutomationFunctionDecorator
    def show_setup_Language(self, litter):
        self.setEnabled(False)
        sl = Setup_Language(self)
        sl.signal.connect(self.sl_emit)
        sl.show()
        LogManager.HLOG.info(f"언어 설정 팝업 열림")

    @AutomationFunctionDecorator
    def show_setup_Field(self, litter):
        self.setEnabled(False)
        sf = Setup_Field(self)
        sf.signal.connect(self.sf_emit)
        sf.show()
        LogManager.HLOG.info("필드 설정 팝업 열림")
    
    @AutomationFunctionDecorator
    def show_setup_TestList(self, litter):
        self.setEnabled(False)
        tl = Setup_TestList(self)
        tl.signal.connect(self.tl_emit)
        tl.show()
        LogManager.HLOG.info("평가 목록 설정 팝업 열림")

    def sl_emit(self, langPath):
        if langPath != []:
            self.menuOpen.clear()
            LogManager.HLOG.info("퀵메뉴 clear")
            for lang, path in langPath:
                subMenu = QAction(lang, self)
                self.menuOpen.addAction(subMenu)
                subMenu.triggered.connect(partial(self.show_imgList, lang, path, subMenu))
            LogManager.HLOG.info("퀵메뉴 갱신 완료")
        self.setEnabled(True)
        LogManager.HLOG.info("언어 설정 팝업 닫힘으로 메인창 활성화")

    def sf_emit(self, fieldList):
        if fieldList != []:
            for i in range(self.field_gridLayout.count()):
                self.field_gridLayout.itemAt(i).widget().deleteLater()
            if fieldList != ["OK"]:
                self.fieldList = fieldList
                LogManager.HLOG.info("기존 필드리스트 삭제")
                self.set_field_gridLayout()
                
                # if self.result != {}:
                #     for val in self.result.values():
                        
                LogManager.HLOG.info("필드리스트 갱신 완료")
        self.setEnabled(True)
        LogManager.HLOG.info("필드 설정 팝업 닫힘으로 메인창 활성화")

    def tl_emit(self, testList):
        if testList != []:
            for i in range(self.testList_groupbox_layout.count()):
                self.testList_groupbox_layout.itemAt(i).widget().deleteLater()
            if testList != ["OK"]:
                self.testList = testList
                LogManager.HLOG.info("기존 평가 목록 삭제")
                self.set_testList_hboxLayout()
                LogManager.HLOG.info("평가 목록 갱신 완료")
        self.setEnabled(True)
        LogManager.HLOG.info("평가 목록 설정 팝업 닫힘으로 메인창 활성화")
        
    @AutomationFunctionDecorator
    def __allPass_clicked(self, litter):
        for idx, pass_radio in enumerate(self.pass_RadioList):
            if idx != len(self.pass_RadioList)-1:
                self.nextImg_bool = False
            else:
                self.nextImg_bool = True
            pass_radio.click()

    @AutomationFunctionDecorator
    def __allFail_clicked(self, litter):
        for idx, fail_radio in enumerate(self.fail_RadioList):
            if idx != len(self.pass_RadioList)-1:
                self.nextImg_bool = False
            else:
                self.nextImg_bool = True
            fail_radio.click()

    @AutomationFunctionDecorator
    def __allNT_clicked(self, litter):
        for idx, nt_radio in enumerate(self.nt_RadioList):
            if idx != len(self.pass_RadioList)-1:
                self.nextImg_bool = False
            else:
                self.nextImg_bool = True
            nt_radio.click()

    @AutomationFunctionDecorator
    def __allNA_clicked(self, litter):
        for idx, na_Radio in enumerate(self.na_RadioList):
            if idx != len(self.pass_RadioList)-1:
                self.nextImg_bool = False
            else:
                self.nextImg_bool = True
            na_Radio.click()

    @AutomationFunctionDecorator
    def __allNull_clicked(self, litter):
        for idx, nl_radio in enumerate(self.nl_RadioList):
            if idx != len(self.pass_RadioList)-1:
                self.nextImg_bool = False
            else:
                self.nextImg_bool = True
            nl_radio.click()

    @AutomationFunctionDecorator
    def set_testList_hboxLayout(self):
        self.pass_RadioList.clear()
        self.fail_RadioList.clear()
        self.nt_RadioList.clear()
        self.na_RadioList.clear()
        self.nl_RadioList.clear()
        self.all_RadioList.clear()
        
        testList_groupbox = QGroupBox("평가 목록")
        testList_groupbox.setFixedHeight(self.bottom_groupbox_fixedHeight)
        
        testList_groupbox_scrollArea = QScrollArea()
        testList_groupbox_widget = QWidget()
        self.testList_groupbox_layout = QHBoxLayout()
        self.testList_hboxLayout = QHBoxLayout(testList_groupbox)
        self.testList_hboxLayout.addWidget(testList_groupbox_scrollArea)

        for i,val in enumerate(self.testList):
            val = str(val)
            globals()[f'testList_groupbox_{i}'] = QGroupBox(val)

            testList_vboxLayout = QVBoxLayout()

            globals()[f'gb{i}_pass'] = QRadioButton("PASS")
            globals()[f'gb{i}_fail'] = QRadioButton("FAIL")
            globals()[f'gb{i}_nt'] = QRadioButton("N/T")
            globals()[f'gb{i}_na'] = QRadioButton("N/A")
            globals()[f'gb{i}_nl'] = QRadioButton("NULL")
            globals()[f'gb{i}_nl'].setChecked(True)
            
            globals()[f'gb{i}_pass'].clicked.connect(self.radioButton_clicked)
            globals()[f'gb{i}_fail'].clicked.connect(self.radioButton_clicked)
            globals()[f'gb{i}_nt'].clicked.connect(self.radioButton_clicked)
            globals()[f'gb{i}_na'].clicked.connect(self.radioButton_clicked)
            
            self.pass_RadioList.append(globals()[f'gb{i}_pass'])
            self.fail_RadioList.append(globals()[f'gb{i}_fail'])
            self.nt_RadioList.append(globals()[f'gb{i}_nt'])
            self.na_RadioList.append(globals()[f'gb{i}_na'])
            self.nl_RadioList.append(globals()[f'gb{i}_nl'])
            self.all_RadioList = self.pass_RadioList + self.fail_RadioList\
                                + self.nt_RadioList + self.na_RadioList + self.nl_RadioList

            # 평가 목록 그룹 자녀 생성
            testList_vboxLayout.addWidget(globals()[f'gb{i}_pass'])
            testList_vboxLayout.addWidget(globals()[f'gb{i}_fail'])
            testList_vboxLayout.addWidget(globals()[f'gb{i}_nt'])
            testList_vboxLayout.addWidget(globals()[f'gb{i}_na'])
            testList_vboxLayout.addWidget(globals()[f'gb{i}_nl'])
            
            if self.imgList == []:
                globals()[f'gb{i}_pass'].setEnabled(False)
                globals()[f'gb{i}_fail'].setEnabled(False)
                globals()[f'gb{i}_nt'].setEnabled(False)
                globals()[f'gb{i}_na'].setEnabled(False)
                globals()[f'gb{i}_nl'].setEnabled(False)

            globals()[f'testList_groupbox_{i}'].setLayout(testList_vboxLayout)

            self.testList_groupbox_layout.addWidget(globals()[f'testList_groupbox_{i}'])
            
        testList_groupbox_widget.setLayout(self.testList_groupbox_layout)
        testList_groupbox_scrollArea.setWidget(testList_groupbox_widget)
        self.bottom_gridLayout.addWidget(testList_groupbox, 0, 0, 1, 4)
            
    def radioButton_clicked(self):
        """라디오 버튼 클릭 시, NULL 갯수 확인하여 NULL이 없으면 다음 이미지로 넘어감
        """
        null_cnt = sum([int(null.isChecked()) for null in self.nl_RadioList])
        if null_cnt == 0 and self.idx < len(self.imgList) - 1 and self.nextImg_bool:
            self.qbuttons[self.idx+1].click()

    def qbutton_clicked(self, idx, button, litter):

        def set_color():            
            clear_result_color = "background-color:rgb(225, 225, 225);"
                
            result_color = "background-color:rgb(147, 112, 219);"       # 보라색

            self.qbuttons[self.pre_idx].setStyleSheet(clear_result_color)
            LogManager.HLOG.info(f"이전 버튼 색상 초기화:rgb(225, 225, 225)")
            button.setStyleSheet(result_color)    
            LogManager.HLOG.info(f"현재 버튼 색상: 보라색,rgb(147, 112, 219)")

            result_count = {
                'pre_idx':[],
                'idx':[]
            }
            # 이전 버튼에 대한 색상 처리
            for testListName in self.testList:
                result_count['pre_idx'].append(self.result[self.pre_idx][testListName])
                result_count['idx'].append(self.result[self.idx][testListName])
            LogManager.HLOG.info(f"색상처리를 위한 변수 result_count:{result_count}, pre_idx:{self.pre_idx}, idx:{self.idx}")

            if len(self.testList) == result_count['pre_idx'].count('PASS'):
                self.qbuttons[self.pre_idx].setStyleSheet("background-color: rgb(62,74,193);") # 블루

            elif len(self.testList) == result_count['pre_idx'].count('FAIL'):
                self.qbuttons[self.pre_idx].setStyleSheet("background-color: rgb(211,44,98);") # 레드

            elif len(self.testList) == result_count['pre_idx'].count('N/A'):
                self.qbuttons[self.pre_idx].setStyleSheet("background-color: rgb(64,128,128)") # 그레이

            elif len(self.testList) == result_count['pre_idx'].count('N/T'):
                self.qbuttons[self.pre_idx].setStyleSheet("background-color: rgb(56,199,81)") # 민트

            elif len(self.testList) == str(self.result[self.pre_idx]).count('NULL'):
                self.qbuttons[self.pre_idx].setStyleSheet("") # 초기화

            elif result_count['pre_idx'].count('PASS') > 0 or result_count['pre_idx'].count('FAIL') or result_count['pre_idx'].count('N/T') > 0 or result_count['pre_idx'].count('N/A') > 0:
                self.qbuttons[self.pre_idx].setStyleSheet("background-color: #FFFF00") # 노랑
            LogManager.HLOG.info("이전 버튼에 대한 색상 처리 완료")

        self.idx = idx
        self.button = button
        
        self.set_left_right_button_state()

        self.statusbar_label.setText(self.clicked_lang + " - " + self.imgList[idx])
        LogManager.HLOG.info(f"statusbar에 이미지명 표시{self.imgList[idx]}")

        self.img_dir = self.langPath + '\\' + self.imgList[idx]
        self.pixmap = QPixmap(self.img_dir)
        self.img = Image.open(self.img_dir)

        self.resize_right_img()
        LogManager.HLOG.info(f"우측에 이미지 표시:{self.img_dir}")

        # 다른 이미지 버튼 누를 때 액션
        if self.pre_idx != idx:
            # self.result에 값 저장하고 기존 데이타 삭제하기
            result_data = self.insert_result(option=True)
            self.result[self.pre_idx] = result_data
            LogManager.HLOG.info(f"다른 이미지 클릭으로 이전 이미지 결과 저장함, self.result:{self.result}")
            
            # self.result에 기존 평가 data로 세팅
            for i,data in enumerate(self.testList):
                if self.result[idx][data] == 'PASS':
                    globals()[f'gb{i}_pass'].setChecked(True)
                elif self.result[idx][data] == 'FAIL':
                    globals()[f'gb{i}_fail'].setChecked(True)
                elif self.result[idx][data] == 'N/T':
                    globals()[f'gb{i}_nt'].setChecked(True)
                elif self.result[idx][data] == 'N/A':
                    globals()[f'gb{i}_na'].setChecked(True)
                else:
                    globals()[f'gb{i}_nl'].setChecked(True)

            for i,data in enumerate(self.fieldList):
                globals()[f'desc_LineEdit{i}'].setText(self.result[idx][data])

        set_color()
        self.pre_idx = idx

    def insert_result(self, option=None):
        """dict에 평가결과 저장하는 함수

        Args:
            option : True 선택 시 화면에 입력되어 있는 데이터 clear

        Returns:
            result_data: 현재 화면에 입력되어 있는 데이터 반환
        """
        result_data = {}
        try:
            result_data["이미지"] = self.result[self.pre_idx]["이미지"]
        except:
            msg = traceback.format_exc()
            LogManager.HLOG.error(msg)

        for i,val in enumerate(self.testList):
            if globals()[f'gb{i}_pass'].isChecked():
                result_data[val] = "PASS"
            elif globals()[f'gb{i}_fail'].isChecked():
                result_data[val] = "FAIL"
            elif globals()[f'gb{i}_nt'].isChecked():
                result_data[val] = "N/T"
            elif globals()[f'gb{i}_na'].isChecked():
                result_data[val] = "N/A"
            else:
                result_data[val] = ""

            if option is True:
                globals()[f'gb{i}_nl'].setChecked(True)

        for i,field in enumerate(self.fieldList):
            result_data[field] = globals()[f'desc_LineEdit{i}'].text()
            # result_data.append(field_data)
            if option is True:
                globals()[f'desc_LineEdit{i}'].clear()

        result_data["버전 정보"] = self.version_textEdit.toPlainText()
        return result_data

    @AutomationFunctionDecorator
    def double_click_img(self, img_dir, e):
        self.viewer = ImageViewer(img_dir)
        self.viewer.show()
        LogManager.HLOG.info(f"이미지 더블클릭:{img_dir}")

    @AutomationFunctionDecorator
    def show_imgList(self, lang, langPath, subMenu="", litter=None):
        """좌측에 표출할 이미지버튼들을 세팅할 함수

        Args:
            lang : 현재 선택된 언어
        """
        # if self.result != {}:
        #     reply = QMessageBox.question(self, '알림', '지금 언어를 변경하면 현재까지의 진행\n취소하시겠습니까?',
        #                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # self.loadingThread.start()
        self.pre_idx = 0
        if lang != self.pre_lang:

            try:
                self.imgList = [fn for fn in os.listdir(langPath)
                        if (fn.endswith('.png') or fn.endswith('.jpg'))]
            except FileNotFoundError:
                QMessageBox.warning(self, "주의", "존재하지 않는 경로입니다.")
                subMenu.setChecked(False)
                return
            
            # self.imgListThread.start()

            if self.imgList == []:
                QMessageBox.warning(self, "주의", "선택하신 경로에 이미지 파일이 없습니다.")
                subMenu.setChecked(False)
            else:
                self.actionSave.setEnabled(True)
                if self.pre_subMenu is not None:
                    self.pre_subMenu.setChecked(False)
                subMenu.setChecked(True)
                self.setEnabled(False)
                # 평가결과 기록 삭제
                self.result.clear()
                self.clicked_lang = lang
                self.setupList = self.testList + self.fieldList

                # 이미지 리스트 초기화
                for i in range(self.img_VBoxLayout.count()):
                    self.img_VBoxLayout.itemAt(i).widget().deleteLater()

                # 선택한 언어 기억
                self.langPath = langPath
                LogManager.HLOG.info(f"이미지 리스트 불러옴, 선택된 언어:{lang}, 경로:{langPath}")

                # 이미지 버튼 추가
                self.qbuttons = {}
                self.icons = {}
                for index, filename in enumerate(self.imgList):
                    # 평가결과를 저장할 dictionary: self.result 세팅
                    self.result[index] = {}
                    self.result[index]['이미지'] = langPath + '\\' + filename
                    for setupListName in self.setupList:
                        self.result[index][setupListName] = ""
                    self.result[index]['버전 정보'] = ""

                    pixmap = QPixmap(langPath + '\\' + filename)
                    pixmap = pixmap.scaled(40, 40, Qt.IgnoreAspectRatio)
                    icon = QIcon()
                    icon.addPixmap(pixmap)
                    self.icons[index] = icon
                    
                    button = QPushButtonIcon()
                    button.setIcon(icon)
                    button.clicked.connect(partial(self.qbutton_clicked, index, button))
                            
                    self.img_VBoxLayout.addWidget(button)
                    self.qbuttons[index] = button
                    QApplication.processEvents()

                LogManager.HLOG.info(f"self.result:{self.result}")
                self.setEnabled(True)
                self.qbuttons[0].click()
                if len(self.imgList) > 1:
                    self.right_imgBtn.setEnabled(True)
                LogManager.HLOG.info(f"이미지 불러온 후 첫번째 버튼 클릭")
                
                self.setEnabled_bottom()
                self.pre_lang = lang
                self.pre_subMenu = subMenu

        else:
            subMenu.setChecked(True)
            
            # self.loadingThread.terminate()
            
    def setEnabled_bottom(self):
        for field in self.field_lineEdit:
            field.setEnabled(True)
        for radio_button in self.all_RadioList:
            radio_button.setEnabled(True)

        self.allPass_RadioButton.setEnabled(True)
        self.allFail_RadioButton.setEnabled(True)
        self.allNT_RadioButton.setEnabled(True)
        self.allNA_RadioButton.setEnabled(True)
        self.allNull_RadioButton.setEnabled(True)
        self.version_textEdit.setEnabled(True)
            
            
    # def start_loading(self):
    #     loading = LoadingMask(self, './image/loading.gif')
    #     loading.show()

    @AutomationFunctionDecorator
    def set_field_gridLayout(self):
        self.field_lineEdit.clear()

        for i,field in enumerate(self.fieldList):
            globals()[f'field_Label{i}'] = QLabel(field)
            globals()[f'desc_LineEdit{i}'] = QLineEdit()
            if i%2==0:
                self.field_gridLayout.addWidget(globals()[f'field_Label{i}'], 0,i)
                self.field_gridLayout.addWidget(globals()[f'desc_LineEdit{i}'], 0,i+1)
            else:
                self.field_gridLayout.addWidget(globals()[f'field_Label{i}'], 1,i-1)
                self.field_gridLayout.addWidget(globals()[f'desc_LineEdit{i}'], 1,i)
            
            self.field_lineEdit.append(globals()[f'desc_LineEdit{i}'])

            if self.imgList == []:
                globals()[f'desc_LineEdit{i}'].setEnabled(False)
            
    
    @AutomationFunctionDecorator
    def btn_onClicked(self, litter):
        btn = self.sender()
        if btn.text() == ">":
            self.qbuttons[self.idx+1].click()
        elif btn.text() == "<":
            self.qbuttons[self.idx-1].click()
        
    def set_left_right_button_state(self):
        """좌우 버튼 활성화/비활성화 함수
        """
        if self.idx == 0:
            self.left_imgBtn.setEnabled(False)
        elif self.idx == len(self.imgList) - 1:
            self.right_imgBtn.setEnabled(False)
        else:
            self.left_imgBtn.setEnabled(True)
            self.right_imgBtn.setEnabled(True)
            
    def resizeEvent(self, event):
        """창 크기가 변경될 때 이미지 사이즈도 변경됨
           try: 처음엔 이미지가 없는 경우 pass

        Args:
            event (_type_): _description_
        """
        try:
            self.resize_right_img()
        except:
            pass
        
    def resize_right_img(self):
        """우측 이미지 사이즈 변경 함수
        """
        if self.img.width < self.img_Label.width() and self.img.height < self.img_Label.height():
            pass
        elif self.img.width/self.img.height < self.img_Label.width()/self.img_Label.height():
            self.pixmap = self.pixmap.scaledToHeight(self.img_Label.height())
        else:
            self.pixmap = self.pixmap.scaledToWidth(self.img_Label.width())

        self.img_Label.setPixmap(QPixmap(self.pixmap))
        self.img_Label.setAlignment(Qt.AlignCenter)
        self.img_Label.mouseDoubleClickEvent = partial(self.double_click_img, self.img_dir)

    def save_result(self):
        """
        결과값을 DB에 저장
        """
        # 현재 이미지에 대한 결과 저장
        result_data = self.insert_result()
        self.result[self.idx] = result_data
        
        # SQLite에 현재 언어 table이 있으면 삭제
        self.c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        sql_tables = self.c.fetchall()
        sql_tables_list = [table[0] for table in sql_tables]
        if self.clicked_lang in sql_tables_list:
            self.c.execute(f"DROP TABLE {self.clicked_lang}")
        LogManager.HLOG.info(f"{self.clicked_lang} 테이블 삭제")

        query = f"CREATE TABLE IF NOT EXISTS '{self.clicked_lang}' ('이미지' TEXT,"
        for i, col in enumerate(self.setupList):
            query += f"'{col}' TEXT,"
        query += "'버전정보' TEXT)"
        LogManager.HLOG.info(f"평가결과 저장 query:{query}")
        
        self.c.execute(query)

        question_marks = ", ".join(['?' for _ in range(len(result_data.keys()))])
        LogManager.HLOG.info(f"저장할 평가결과:{self.result}")
        
        for i in self.result.values():
            try:
                self.dbConn.execute(f"INSERT INTO {self.clicked_lang} VALUES ({question_marks})", 
                        (tuple(i.values())))
                self.dbConn.commit()
            except RuntimeError:
                continue

    @AutomationFunctionDecorator
    def closeEvent(self, e) -> None:
        try:
            self.c.execute(f"SELECT * FROM {self.clicked_lang}")
            sql_result = self.c.fetchall()
        except:
            sql_result = []
        result_list = []
        
        for vals in self.result.values():
            result = []
            for val in vals.values():
                result.append(val)
            result_list.append(tuple(result))
        
        if sql_result != result_list:
            reply = QMessageBox.question(self, '알림', '평가결과가 저장되지 않았습니다.\n저장하고 끄겠습니까?',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.save_result()
        
        e.accept()
        

#     # # 0728
#     # # 키보드 설정
#     # 
#     @AutomationFunctionDecorator
#     def keyReleaseEvent(self, a0: QKeyEvent) -> None:

#         VERVUAL_NATIVE_LEFTKEY = 37
#         VERVUAL_NATIVE_RIGHTKEY = 39

#         if a0.nativeVirtualKey() == VERVUAL_NATIVE_LEFTKEY:
#                 self.btn_onClicked(False)
            
#         elif a0.nativeVirtualKey() == VERVUAL_NATIVE_RIGHTKEY:
#             self.btn_onClicked(True)
                
class QPushButtonIcon(QPushButton):
    
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setIconSize(QSize(40, 40))

# class LoadingMask(QMainWindow):
#     def __init__(self, parent, gif=None, tip=None):
#         super(LoadingMask, self).__init__(parent)

#         parent.installEventFilter(self)

#         self.label = QLabel()

#         if not tip is None:
#             self.label.setText(tip)
#             font = QFont('Microsoft YaHei', 10, QFont.Normal)
#             font_metrics = QFontMetrics(font)
#             self.label.setFont(font)
#             self.label.setFixedSize(font_metrics.width(tip, len(tip))+10, font_metrics.height()+5)
#             self.label.setAlignment(Qt.AlignCenter)
#             self.label.setStyleSheet(
#                 'QLabel{background-color: rgba(0,0,0,70%);border-radius: 4px; color: white; padding: 5px;}')

#         if not gif is None:
#             self.movie = QMovie(gif)
#             self.label.setMovie(self.movie)
#             self.label.setFixedSize(QSize(160, 160))
#             self.label.setScaledContents(True)
#             self.movie.start()

#         layout = QHBoxLayout()
#         widget = QWidget()
#         widget.setLayout(layout)
#         layout.addWidget(self.label)

#         self.setCentralWidget(widget)
#         self.setWindowOpacity(0.8)
#         self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
#         self.hide()

#     def eventFilter(self, widget, event):
#         if widget == self.parent() and type(event) == QMoveEvent:
#             self.moveWithParent()
#             return True
#         return super(LoadingMask, self).eventFilter(widget, event)

#     def moveWithParent(self):
#         if self.isVisible():
#             self.move(self.parent().geometry().x(), self.parent().geometry().y())
#             self.setFixedSize(QSize(self.parent().geometry().width(), self.parent().geometry().height()))
            
# class LoadingThread(QThread):
#     loading_singnal = pyqtSignal()
#     def run(self):
#         self.loading_singnal.emit()
        
# class imgListThread(QThread):
#     imgList_singnal = pyqtSignal()
#     def run(self):
#         self.imgList_singnal.emit()

def Init():
    LogManager.Init()

if __name__ == "__main__":
    Init()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("modim1.png"))
    ui = MainWindow()
    ui.show()
    sys.exit(app.exec_())
