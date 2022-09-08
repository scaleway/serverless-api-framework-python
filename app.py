class App:
    def func(self, **kwargs):
        def decorator(handler):
            def _inner():
                print(kwargs)
                return handler()

            return _inner

        return decorator


app = App()


@app.func(url="/")
def hello_world():
    return "Hello World!"


print(hello_world())
