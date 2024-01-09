import bpy

def add_driver_variable(driver, id, data_path, name, id_type='OBJECT', custom_property = True):
    var = driver.variables.new()
    var.name = name
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = id_type
    var.targets[0].id = id
    var.targets[0].data_path = f'["{data_path}"]' if custom_property else data_path
    
def copy_driver(src, dst):
    """
    Copy all attributes of the source driver to an empty destination driver
    """
    dst.type = src.type
    for src_var in src.variables:
        dst_var = dst.variables.new()
        dst_var.name = src_var.name
        dst_var.type = src_var.type
        dst_var.targets[0].id_type = src_var.targets[0].id_type
        dst_var.targets[0].id = src_var.targets[0].id
        dst_var.targets[0].data_path = src_var.targets[0].data_path
    dst.expression = src.expression