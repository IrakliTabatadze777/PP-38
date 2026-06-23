

class AppConfig:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.debug = True
            cls._instance.max_retries = 3
            cls._instance.log_file = "app.log"

        return cls._instance

    def show(self):
        print(f"debug={self.debug}, retries={self.max_retries}, log={self.log_file}")



app_config_1 = AppConfig()
app_config_2 = AppConfig()

print(id(app_config_1))
print(id(app_config_2))

app_config_1.show()
app_config_1.debug = False


app_config_2.show()


