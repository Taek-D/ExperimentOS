try:
    with open("output.log", "rb") as f:
        data = f.read()
    text = data.decode("utf-8", errors="replace")
    print(text)
except Exception as e:
    print(e)
