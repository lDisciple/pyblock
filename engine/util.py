from xml.etree import ElementTree

block_template_imports = "from blocks.block import pyblock\n\n\n"
block_template_function = """@pyblock(category="{category}", is_predefined=True)
def {name}():
    pass
"""


def noop(*args, **kwargs):
    pass


async def anoop(*args, **kwargs):
    pass


def create_blocks_from_xml(toolbox_path: str):
    toolbox_xml = ElementTree.parse(toolbox_path)
    current_category = "unknown"
    categories = {"unknown": []}
    for element in toolbox_xml.iter():
        if element.tag == "category":
            current_category = element.get("id")
            if current_category not in categories:
                categories[current_category] = []
        if element.tag == "block":
            block_type = element.get("type")
            categories[current_category].append(block_template_function.format(
                category=current_category,
                name=block_type
            ))
    for category, blocks in categories.items():
        with open(f"lib/blocks/{category}.py", "w") as f:
            f.write(block_template_imports)
            f.write("\n\n".join(blocks))
            f.write("\n")


if __name__ == '__main__':
    pass
    # create_blocks_from_xml("/home/jonathan/Projects/personal/pyblock/editor/src/assets/toolbox.xml")
