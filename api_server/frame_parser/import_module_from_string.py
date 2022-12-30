import sys
import importlib.util
from types import ModuleType

kek = 'sad'

def import_module_from_string(name: str, content: str):
    """

    Args:
        name (str): module name
        source (str): module content

    Raises:
        ImportError: when importlib.util.spec_from_loader returns None

    Returns:
        ModuleType: imported module object
    """
    spec = importlib.util.spec_from_loader(name, loader=None)
    if spec is not None:
        module: ModuleType = importlib.util.module_from_spec(spec)
        # glob = {key: val for key, val in globals().items() if not key.startswith('__')} # внешние переменные и функции
        # exec(content, module.__dict__, module.__dict__.update(**glob))  #  захватывает внешние переменные и функции
        exec(content, module.__dict__)  # не захватывает внешние переменные и функции
        sys.modules[name] = module
        return module
    raise ImportError(f'There is no module with name {name}')



my_module = import_module_from_string('hello_module',
'''
# print(f'{kek}')
def hello():
    print('hello world')
''')


if __name__ == '__main__':
    # print(sys.modules)
    my_module.hello()
    # del hello_module
    # print(sys.modules)
    # my_module.hello()