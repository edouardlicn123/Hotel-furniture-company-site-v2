import smtplib
from email.mime.text import MIMEText

try:
    server = smtplib.SMTP_SSL('smtp.163.com', 465, timeout=20)
    server.login('15007578643@163.com', 'QJQAn6QZqbbkpfm4')
    print("登录成功！")

    msg = MIMEText("命令行测试", 'plain', 'utf-8')
    msg['From'] = '15007578643@163.com'
    msg['To'] = 'edouardlicn@gmail.com'
    msg['Subject'] = "163 SMTP 测试"

    server.send_message(msg)
    print("发送成功！")
    server.quit()
except Exception as e:
    print("失败:", e)
