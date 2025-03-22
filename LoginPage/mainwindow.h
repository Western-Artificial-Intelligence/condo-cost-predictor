#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QStackedWidget>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

/**
 * @author kevin liu
 * @brief main window class for the app
 */
class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    /**
     * @brief sets up the main window
     * @param parent optional parent widget
     */
    MainWindow(QWidget *parent = nullptr);

    /**
     * @brief cleans up ui stuff
     */
    ~MainWindow();

private slots:
    /**
     * @brief handles login button click
     */
    void on_loginButton_clicked();

    /**
     * @brief switches to forgot password page
     */
    void on_forgotButton_clicked();

    /**
     * @brief switches to help page
     */
    void on_helpButton_clicked();

    /**
     * @brief goes back to main page
     */
    void on_backButton_2_clicked();

    /**
     * @brief goes back to main page
     */
    void on_backButton_clicked();

    /**
     * @brief goes back to main page
     */
    void on_backButton_3_clicked();

    /**
     * @brief handles password retrieval
     */
    void on_retrieveButton_clicked();

private:
    Ui::MainWindow *ui; ///< ui stuff
    QStackedWidget *stackedWidget; ///< widget for managing pages
};

#endif // MAINWINDOW_H
