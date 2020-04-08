import jinja2


class Manual:
    def __init__(self, dict):
        self._dict = dict

    def generate(self, filename):
        templateLoader = jinja2.FileSystemLoader(searchpath="./")
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template("templates/manual.jinja2")
        with open(filename, "w") as f:
            f.write(template.render(self._dict))