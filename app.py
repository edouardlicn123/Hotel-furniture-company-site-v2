from app import create_app

app = create_app()

# 明確指定 host/port，並關掉重載器第一次啟動時的干擾
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',          # 允許本地所有介面
        port=5000,
        debug=True,
        use_reloader=False,      # ← 這行很關鍵！第一次啟動不要用 reloader
        threaded=True            # 多執行緒，更快回應第一次請求
    )


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')
