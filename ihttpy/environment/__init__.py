import os


app = os.getenv("app")

if app == "dev":
    MODE = 'Development'
    import ihttpy.environment.dev as config
elif app == "prod":
    MODE = 'Production'
    import ihttpy.environment.prod as config
else:
    raise ValueError(f"environment variable $app should have been either "
                     f"`dev` or `prod`. got:{app}:")

__all__ = ['MODE', 'BACKEND_ADDRESS', 'FRONTEND_ADDRESS']
# todo dynamic __all__ load with environment variables
BACKEND_ADDRESS = config.BACKEND_ADDRESS
FRONTEND_ADDRESS = config.FRONTEND_ADDRESS
# for name in dir(config):
#     if not name.startswith("__"):
#         __all__.append(name)

