#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QMessageBox>
#include <QStackedWidget>
#include <QVBoxLayout>

/**
 * @author kevin liu
 * @brief sets up the main window
 * @param parent optional parent widget, usually null
 */
MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    stackedWidget = new QStackedWidget(this);

    stackedWidget->addWidget(ui->centralwidget);

    /**
     * @brief adds help page (index 1) to stacked widget
     */
    QWidget *page2 = ui->page2;
    stackedWidget->addWidget(page2);

    /**
     * @brief adds login success page (index 2) to stacked widget
     */
    QWidget *page3 = ui->page3;
    stackedWidget->addWidget(page3);

    /**
     * @brief adds forgot password page (index 3) to stacked widget
     */
    QWidget *page4 = ui->page4;
    stackedWidget->addWidget(page4);

    setCentralWidget(stackedWidget);
}

/**
 * @brief cleans up ui when closing
 */
MainWindow::~MainWindow()
{
    delete ui;
}

/**
 * @brief opens help page
 */
void MainWindow::on_helpButton_clicked()
{
    stackedWidget->setCurrentIndex(1);
}

/**
 * @brief goes back to main page from help
 */
void MainWindow::on_backButton_2_clicked()
{
    stackedWidget->setCurrentIndex(0);
}

/**
 * @note the correct username for now is is "admin" all lowercase, and the password is "1234"
 * @brief checks login info, shows success or error
 */
void MainWindow::on_loginButton_clicked()f
{
    QString username = ui->usernameLineEdit->text();
    QString password = ui->passwordLineEdit->text();

    if (username == "admin" && password == "1234") {
        QMessageBox::information(this, "login successful", "welcome!");
        stackedWidget->setCurrentIndex(2);
    } else {
        QMessageBox::warning(this, "login failed", "wrong username or password");
    }
}

/**
 * @brief goes back to main page from login success
 */
void MainWindow::on_backButton_clicked()
{
    stackedWidget->setCurrentIndex(0);
}

/**
 * @brief goes back to main page from forgot password
 */
void MainWindow::on_backButton_3_clicked()
{
    stackedWidget->setCurrentIndex(0);
}

/**
 * @brief checks username, shows password if correct
 */
void MainWindow::on_retrieveButton_clicked()
{
    QString username = ui->NameLineEdit_2->text();

    if (username == "admin") {
        QMessageBox::information(this, "your password is", "1234");
    } else {
        QMessageBox::warning(this, "error", "username not found");
    }
}

/**
 * @brief opens forgot password page
 */
void MainWindow::on_forgotButton_clicked()
{
    stackedWidget->setCurrentIndex(3);
}
