def clear():
    """remove all the pieces from the current node."""
    node = hou.pwd() 
    m = node.parm("points")
    
    mi = m.multiParmInstancesPerItem()
    mc = m.multiParmInstancesCount()
    
    while mc >= mi:
        m.removeMultiParmInstance(0)
        mc = m.multiParmInstancesCount() 

        
def add_node():
    """append a new Lego Builder node."""
    node = hou.pwd()
    
    #create node with the same parameters
    new_node = node.createOutputNode("lego_builder")
    new_node.parmTuple("color_vis").set(node.parmTuple("color_vis").eval())
    new_node.parmTuple("size_vis").set(node.parmTuple("size_vis").eval())
    new_node.parmTuple("angles").set(node.parmTuple("angles").eval())
    new_node.parmTuple("pp_vis").set(node.parmTuple("pp_vis").eval()) 
    new_node.parmTuple("switch").set(node.parmTuple("switch").eval()) 
    new_node.parmTuple("sizex").set(node.parmTuple("sizex").eval())
    new_node.parmTuple("rcolor").set(node.parmTuple("rcolor").eval())
    
    #select the new node
    new_node.setSelected(1, clear_all_selected=True)
    new_node.setRenderFlag(1)
    new_node.setDisplayFlag(1)