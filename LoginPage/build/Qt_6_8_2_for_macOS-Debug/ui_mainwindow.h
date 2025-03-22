/********************************************************************************
** Form generated from reading UI file 'mainwindow.ui'
**
** Created by: Qt User Interface Compiler version 6.8.2
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_MAINWINDOW_H
#define UI_MAINWINDOW_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QFrame>
#include <QtWidgets/QLabel>
#include <QtWidgets/QLineEdit>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QMenuBar>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QStackedWidget>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_MainWindow
{
public:
    QWidget *centralwidget;
    QStackedWidget *stackedWidget;
    QWidget *page1;
    QPushButton *helpButton;
    QLabel *label;
    QPushButton *loginButton;
    QLabel *label_6;
    QLabel *label_3;
    QFrame *frame;
    QLineEdit *NameLineEdit;
    QPushButton *forgotButton;
    QLabel *label_5;
    QLineEdit *usernameLineEdit;
    QLineEdit *passwordLineEdit;
    QLabel *label_2;
    QWidget *page3;
    QLabel *label_11;
    QPushButton *backButton;
    QLabel *label_13;
    QWidget *page2;
    QLabel *label_7;
    QLabel *label_8;
    QPushButton *backButton_2;
    QLabel *label_9;
    QLabel *label_10;
    QWidget *page4;
    QLabel *label_12;
    QPushButton *backButton_3;
    QLabel *label_14;
    QLineEdit *NameLineEdit_2;
    QPushButton *retrieveButton;
    QMenuBar *menubar;
    QStatusBar *statusbar;

    void setupUi(QMainWindow *MainWindow)
    {
        if (MainWindow->objectName().isEmpty())
            MainWindow->setObjectName("MainWindow");
        MainWindow->resize(1027, 690);
        QFont font;
        font.setFamilies({QString::fromUtf8(".AppleSystemUIFont")});
        MainWindow->setFont(font);
        MainWindow->setStyleSheet(QString::fromUtf8("QWidget {\n"
"    background-color: #2D2D2D;\n"
"}\n"
""));
        centralwidget = new QWidget(MainWindow);
        centralwidget->setObjectName("centralwidget");
        stackedWidget = new QStackedWidget(centralwidget);
        stackedWidget->setObjectName("stackedWidget");
        stackedWidget->setGeometry(QRect(10, 0, 991, 621));
        page1 = new QWidget();
        page1->setObjectName("page1");
        helpButton = new QPushButton(page1);
        helpButton->setObjectName("helpButton");
        helpButton->setGeometry(QRect(689, 490, 51, 41));
        helpButton->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"    background-color: white;\n"
"    color: #2D2D2D;\n"
"    border-radius: 17px; \n"
"	font-family: \"Century Gothic\", sans-serif;\n"
"	font-size: 20px;\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
""));
        label = new QLabel(page1);
        label->setObjectName("label");
        label->setGeometry(QRect(370, 310, 71, 16));
        label->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background: transparent;\n"
"    color: gray;\n"
"	font-size: 11px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"}\n"
""));
        loginButton = new QPushButton(page1);
        loginButton->setObjectName("loginButton");
        loginButton->setGeometry(QRect(370, 460, 261, 32));
        loginButton->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"    background-color: #57B9FF;\n"
"    color: white;\n"
"    border-radius: 15px;\n"
"    font-family: \"Century Gothic\", sans-serif;\n"
"}\n"
""));
        label_6 = new QLabel(page1);
        label_6->setObjectName("label_6");
        label_6->setGeometry(QRect(360, 90, 361, 51));
        QFont font1;
        font1.setFamilies({QString::fromUtf8("Impact")});
        font1.setBold(true);
        label_6->setFont(font1);
        label_6->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color: white;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 40px;\n"
"font-family: \"Impact\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        label_3 = new QLabel(page1);
        label_3->setObjectName("label_3");
        label_3->setGeometry(QRect(370, 250, 71, 16));
        label_3->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background: transparent;\n"
"    color: gray;\n"
"	font-size: 11px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"}\n"
""));
        frame = new QFrame(page1);
        frame->setObjectName("frame");
        frame->setGeometry(QRect(330, 160, 341, 371));
        frame->setStyleSheet(QString::fromUtf8("QFrame {\n"
"    background-color: white; \n"
"    border: 0px solid lightgray; \n"
"    border-radius: 50px; \n"
"    padding: 10px; \n"
"}\n"
""));
        frame->setFrameShape(QFrame::Shape::StyledPanel);
        frame->setFrameShadow(QFrame::Shadow::Raised);
        NameLineEdit = new QLineEdit(frame);
        NameLineEdit->setObjectName("NameLineEdit");
        NameLineEdit->setGeometry(QRect(40, 110, 261, 31));
        NameLineEdit->setStyleSheet(QString::fromUtf8("QLineEdit {\n"
"background-color: white; \n"
"color: black; \n"
"border: 2px solid lightgray;\n"
"border-radius: 15px; \n"
"padding: 5px;\n"
"\n"
"}\n"
"\n"
"\n"
"\n"
""));
        forgotButton = new QPushButton(frame);
        forgotButton->setObjectName("forgotButton");
        forgotButton->setGeometry(QRect(193, 264, 121, 32));
        forgotButton->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"    background-color: none; \n"
"    color: grey; \n"
"	font-size: 10px;\n"
"    border-radius: 15px; \n"
" font-family: \"Century Gothic\", sans-serif;\n"
"\n"
"}\n"
""));
        label_5 = new QLabel(frame);
        label_5->setObjectName("label_5");
        label_5->setGeometry(QRect(100, 30, 151, 51));
        label_5->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color:  #2D2D2D;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 25px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        usernameLineEdit = new QLineEdit(frame);
        usernameLineEdit->setObjectName("usernameLineEdit");
        usernameLineEdit->setGeometry(QRect(40, 170, 261, 31));
        usernameLineEdit->setStyleSheet(QString::fromUtf8("QLineEdit {\n"
"background-color: white; \n"
"color: black; \n"
"border: 2px solid lightgray;\n"
"border-radius: 15px; \n"
"padding: 5px;\n"
"}\n"
"\n"
""));
        passwordLineEdit = new QLineEdit(frame);
        passwordLineEdit->setObjectName("passwordLineEdit");
        passwordLineEdit->setGeometry(QRect(40, 230, 261, 31));
        passwordLineEdit->setStyleSheet(QString::fromUtf8("QLineEdit {\n"
"background-color: white; \n"
"color: black; \n"
"border: 2px solid lightgray;\n"
"border-radius: 15px; \n"
"padding: 5px;\n"
"}\n"
"\n"
""));
        passwordLineEdit->setEchoMode(QLineEdit::EchoMode::Password);
        label_2 = new QLabel(page1);
        label_2->setObjectName("label_2");
        label_2->setGeometry(QRect(370, 370, 60, 16));
        label_2->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background: transparent;\n"
"    color: gray;\n"
"	font-size: 11px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"}\n"
""));
        stackedWidget->addWidget(page1);
        frame->raise();
        helpButton->raise();
        label->raise();
        loginButton->raise();
        label_6->raise();
        label_3->raise();
        label_2->raise();
        page3 = new QWidget();
        page3->setObjectName("page3");
        label_11 = new QLabel(page3);
        label_11->setObjectName("label_11");
        label_11->setGeometry(QRect(380, 220, 261, 51));
        label_11->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color:  white;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 25px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        backButton = new QPushButton(page3);
        backButton->setObjectName("backButton");
        backButton->setGeometry(QRect(420, 370, 151, 41));
        backButton->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"    background-color: white;\n"
"    color: #2D2D2D;\n"
"    border-radius: 17px; \n"
"	font-family: \"Century Gothic\", sans-serif;\n"
"	font-size: 15px;\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
""));
        label_13 = new QLabel(page3);
        label_13->setObjectName("label_13");
        label_13->setGeometry(QRect(392, 270, 261, 51));
        label_13->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color:  white;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 15px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        stackedWidget->addWidget(page3);
        page2 = new QWidget();
        page2->setObjectName("page2");
        label_7 = new QLabel(page2);
        label_7->setObjectName("label_7");
        label_7->setGeometry(QRect(420, 110, 151, 51));
        label_7->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color:  white;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 25px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        label_8 = new QLabel(page2);
        label_8->setObjectName("label_8");
        label_8->setGeometry(QRect(220, 130, 731, 131));
        label_8->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color:  white;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 15px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        backButton_2 = new QPushButton(page2);
        backButton_2->setObjectName("backButton_2");
        backButton_2->setGeometry(QRect(440, 380, 121, 41));
        backButton_2->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"    background-color: white;\n"
"    color: #2D2D2D;\n"
"    border-radius: 17px; \n"
"	font-family: \"Century Gothic\", sans-serif;\n"
"	font-size: 15px;\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
""));
        label_9 = new QLabel(page2);
        label_9->setObjectName("label_9");
        label_9->setGeometry(QRect(230, 160, 581, 131));
        label_9->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color:  white;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 15px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        label_10 = new QLabel(page2);
        label_10->setObjectName("label_10");
        label_10->setGeometry(QRect(398, 190, 581, 131));
        label_10->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color:  white;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 15px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        stackedWidget->addWidget(page2);
        page4 = new QWidget();
        page4->setObjectName("page4");
        label_12 = new QLabel(page4);
        label_12->setObjectName("label_12");
        label_12->setGeometry(QRect(390, 180, 261, 51));
        label_12->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color:  white;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 25px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        backButton_3 = new QPushButton(page4);
        backButton_3->setObjectName("backButton_3");
        backButton_3->setGeometry(QRect(340, 380, 151, 41));
        backButton_3->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"    background-color: white;\n"
"    color: #2D2D2D;\n"
"    border-radius: 17px; \n"
"	font-family: \"Century Gothic\", sans-serif;\n"
"	font-size: 15px;\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
""));
        label_14 = new QLabel(page4);
        label_14->setObjectName("label_14");
        label_14->setGeometry(QRect(300, 250, 431, 51));
        label_14->setStyleSheet(QString::fromUtf8("QLabel {\n"
"    background-color: none;\n"
"    color:  white;\n"
"    border: 0px solid gray;\n"
"    border-radius: 10px;\n"
"    padding: 5px;\n"
"    font-size: 15px;\n"
" font-family: \"Century Gothic\", sans-serif;\n"
"    font-weight: bold;\n"
"}\n"
""));
        NameLineEdit_2 = new QLineEdit(page4);
        NameLineEdit_2->setObjectName("NameLineEdit_2");
        NameLineEdit_2->setGeometry(QRect(370, 310, 261, 31));
        NameLineEdit_2->setStyleSheet(QString::fromUtf8("QLineEdit {\n"
"background-color: white; \n"
"color: black; \n"
"border: 2px solid lightgray;\n"
"border-radius: 15px; \n"
"padding: 5px;\n"
"\n"
"}\n"
"\n"
"\n"
"\n"
""));
        retrieveButton = new QPushButton(page4);
        retrieveButton->setObjectName("retrieveButton");
        retrieveButton->setGeometry(QRect(510, 380, 151, 41));
        retrieveButton->setStyleSheet(QString::fromUtf8("QPushButton {\n"
"    background-color: white;\n"
"    color: #2D2D2D;\n"
"    border-radius: 17px; \n"
"	font-family: \"Century Gothic\", sans-serif;\n"
"	font-size: 15px;\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
""));
        stackedWidget->addWidget(page4);
        MainWindow->setCentralWidget(centralwidget);
        menubar = new QMenuBar(MainWindow);
        menubar->setObjectName("menubar");
        menubar->setGeometry(QRect(0, 0, 1027, 24));
        MainWindow->setMenuBar(menubar);
        statusbar = new QStatusBar(MainWindow);
        statusbar->setObjectName("statusbar");
        MainWindow->setStatusBar(statusbar);

        retranslateUi(MainWindow);

        stackedWidget->setCurrentIndex(0);


        QMetaObject::connectSlotsByName(MainWindow);
    } // setupUi

    void retranslateUi(QMainWindow *MainWindow)
    {
        MainWindow->setWindowTitle(QCoreApplication::translate("MainWindow", "MainWindow", nullptr));
        helpButton->setText(QCoreApplication::translate("MainWindow", "?", nullptr));
        label->setText(QCoreApplication::translate("MainWindow", "Username", nullptr));
        loginButton->setText(QCoreApplication::translate("MainWindow", "Log In", nullptr));
        label_6->setText(QCoreApplication::translate("MainWindow", "NAS Application", nullptr));
        label_3->setText(QCoreApplication::translate("MainWindow", "Name", nullptr));
        forgotButton->setText(QCoreApplication::translate("MainWindow", "Forgot Password", nullptr));
        label_5->setText(QCoreApplication::translate("MainWindow", "Welcome", nullptr));
        label_2->setText(QCoreApplication::translate("MainWindow", "Password", nullptr));
        label_11->setText(QCoreApplication::translate("MainWindow", "Log in Successful", nullptr));
        backButton->setText(QCoreApplication::translate("MainWindow", "Back to Log In", nullptr));
        label_13->setText(QCoreApplication::translate("MainWindow", "<connect to home page>", nullptr));
        label_7->setText(QCoreApplication::translate("MainWindow", "Help page", nullptr));
        label_8->setText(QCoreApplication::translate("MainWindow", "This project creates a local file storage system using a Raspberry Pi with a", nullptr));
        backButton_2->setText(QCoreApplication::translate("MainWindow", "Back", nullptr));
        label_9->setText(QCoreApplication::translate("MainWindow", "desktop app for uploading, downloading, and managing files securely.", nullptr));
        label_10->setText(QCoreApplication::translate("MainWindow", "<insert more instructions>", nullptr));
        label_12->setText(QCoreApplication::translate("MainWindow", "Forgot Password", nullptr));
        backButton_3->setText(QCoreApplication::translate("MainWindow", "Back to Log In", nullptr));
        label_14->setText(QCoreApplication::translate("MainWindow", "Enter your username and we will retrieve your password:", nullptr));
        retrieveButton->setText(QCoreApplication::translate("MainWindow", "Retrieve Password", nullptr));
    } // retranslateUi

};

namespace Ui {
    class MainWindow: public Ui_MainWindow {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MAINWINDOW_H
