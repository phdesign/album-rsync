class Folder:

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.full_path = kwargs.get('full_path')
        self.is_root = False

    def __repr__(self):
        return "Folder: {{id={}, name={}}}".format(self.id, self.name)

class RootFolder(Folder):

    def __init__(self):
        super(RootFolder, self).__init__(id=None, name='', full_path=None)
        self.is_root = True
