"""
State:          Pau::lego builder::1.0
Author:         Pau
Date Created:   March 05, 2024 - 21:39:08
"""

# Third-party modules
import hou
import viewerstate.utils as su

class State(object):
    # set info panel
    HUD_TEMPLATE = {
        "title": "Lego Builder", "desc": "tool", "icon": "opdef:/Pau::Sop/lego_builder::1.0?IconImage",
        "rows": [
            {"id": "add", "label": "Add Piece", "key": "LMB"},
            {"id": "remove", "label": "Delete Piece", "key": "Ctrl LMB"},
            {"id": "scroll", "label": "Change Piece Type", "key": "mousewheel"},
            {"id": "increase", "label": "Increase Size", "key": "+"},
            {"id": "decrease", "label": "Decrease Size", "key": "-"},
            {"id": "color", "label": "Select Color", "key": "c"},
            {"id": "rotate", "label": "Rotate Piece", "key": "x"},
            {"id": "pivot", "label": "Change Pivot Point", "key": "z"},

        ]
    }
    
    # Prompt message
    MSG = "LMB to add LEGO piece."   

    def __init__(self, state_name, scene_viewer):
        self.state_name = state_name
        self.scene_viewer = scene_viewer
        
        self.pressed = False
        self.index = 0    
        self.node = None
        self.geometry = None
        self.switch = None
       
    def pointCount(self):
        try:
            self.switch = self.node.parm("switch").eval()
            multiparm = self.node.parm(f"points")
            return multiparm.evalAsInt()
        except:
            return 0

    def start(self):        
        if not self.pressed:
            self.scene_viewer.beginStateUndo("Add point")
            self.index = self.pointCount()
            multiparm = self.node.parm(f"points")
            multiparm.insertMultiParmInstance(self.index)     
            self.pressed = True

    def finish(self):
        if self.pressed:
            self.scene_viewer.endStateUndo()
        self.pressed = False

    def onEnter(self, kwargs):
        """Method called when entering the state."""
        
        self.node = kwargs["node"]
        
        # start info panels
        self.scene_viewer.hudInfo(template=self.HUD_TEMPLATE)
        
        # create variable
        self.angle = self.node.parm("angles").evalAsInt()
        self.color = self.node.parmTuple("color_vis").eval()
        self.size = self.node.parm("size_vis").evalAsInt()
        self.pivot = self.node.parm("pp_vis").evalAsInt()
        
        # save geo in a variable
        self.geometry = self.node.geometry()
        
        # enable snapping
        self.current_snap = self.scene_viewer.snappingMode()
        self.scene_viewer.setSnappingMode(hou.snappingMode.Point)
        
        # show guide pts
        self.node.parm("remove_pts").set(0)
        
        if not self.node:
            raise

        self.scene_viewer.setPromptMessage(State.MSG)
        
    def onExit(self, kwargs):
        """Method called when exiting the state."""     
        # delete guide pts
        self.node.parm("remove_pts").set(1)
        
        # return to previuous snapping
        self.scene_viewer.setSnappingMode(self.current_snap) 
        
    def onInterrupt(self,kwargs):      
        """Method called when the state is interrupted."""
        self.finish()

    def onResume(self, kwargs):
        """Method called when the state resumes."""
        self.scene_viewer.setPromptMessage( State.MSG )
    
    def onKeyEvent(self, kwargs):
        """Method to handle keyboard events."""
        ui_event = kwargs["ui_event"].device()
        keyboard_str = ui_event.keyString()
               
        # select color
        if keyboard_str == "c":
            try:
                self.color = hou.ui.selectColor().rgb() 
                return True
            except:
                return True
                                
        # select rotation angle    
        if keyboard_str == "x":                    
            self.angle += 90
            self.node.parm("angles").set(self.angle)
            return True
            
        if keyboard_str == "+" and self.size<5:
            # reset pivot point before scale
            self.node.parm("pp_vis").set(0)
            self.pivot = self.node.parm("pp_vis").evalAsInt()
            # scale up
            self.size += 1
            self.node.parm("size_vis").set(self.size)
            return True  
            
        if keyboard_str == "-" and self.size>1:
            # reset pivot point before scale
            self.node.parm("pp_vis").set(0)
            self.pivot = self.node.parm("pp_vis").evalAsInt()
            # scale down
            self.size -= 1
            self.node.parm("size_vis").set(self.size)
            return True  
            
        # change pivot point    
        if keyboard_str == "z":                    
            self.pivot += 1
            self.node.parm("pp_vis").set(self.pivot)
            return True
        return False
                             
    def onMouseWheelEvent(self, kwargs):  
        """Method to handle mouse wheel events."""
        ui_event = kwargs["ui_event"]
        dev = ui_event.device()
        
        # change type of piece scrolling mouse wheel
        scroll = dev.mouseWheel()
        value = self.node.parm("switch").eval()+scroll
        self.node.parm("switch").set(value)
                   
    def onMouseEvent(self, kwargs):
        """Method to handle mouse events."""
        ui_event = kwargs["ui_event"]
        device = ui_event.device()
        collide = self.node.parm("collide").eval()
       
        # origin value and position of the "camera ray" 
        origin, direction = ui_event.ray()
        
        # snap dictionary values
        snap_dict = ui_event.snappingRay()  
        
        if snap_dict["snapped"]:
            point_index = snap_dict["point_index"]
            
            point = self.geometry.point(point_index)
            point_position = point.position()
        
        # calculate intersect position with geometry
        intersect_geo = su.sopGeometryIntersection(self.geometry, origin, direction)
        intersect_geo_pos = intersect_geo[1]

        # calculate intersect position with grid
        position = su.cplaneIntersection(self.scene_viewer, origin, direction)
        
        # piece Visualizer 
        if snap_dict["snapped"]:
            self.node.parmTuple("mouse_pos").set(point_position)
        else:
            self.node.parmTuple("mouse_pos").set(position)
        self.node.parmTuple("color_vis").set(self.color) 
        
        # create/move point if LMB is down
        if device.isLeftButton() and snap_dict["snapped"] and device.isCtrlKey()==0 and collide==0:
            self.start()
            # create point
            self.node.parm(f"usept{self.index}").set(1)
            # set the point position
            self.node.parmTuple(f"pt{self.index}").set(point_position)
            # set variant piece
            self.node.parm(f"variant{self.index}").set(self.switch)
            # set color
            self.node.parmTuple(f"color{self.index}").set(self.color)
            # set rotation
            self.node.parm(f"rotate{self.index}").set(self.angle) 
            # set size
            self.node.parm(f"size{self.index}").set(self.size)
            # set pivot point
            self.node.parm(f"pp{self.index}").set(self.pivot)

        else:
            self.finish()

        if device.isCtrlKey():
            self.node.parm("ctrl").set(1)
            
        else:
            self.node.parm("ctrl").set(0)
            
        # remove point from MuliParm when Ctrl
        if device.isLeftButton() and device.isCtrlKey() and not intersect_geo[0]==-1:   
            try:
                geo_index = intersect_geo[0]                      
                self.node.parm("points").removeMultiParmInstance(geo_index)
                return True
            except:
                print(f"ERROR: You are trying to remove a piece from another node (current node: {self.node.name()})")
                return True

def createViewerStateTemplate():
    """Function to create the viewer state template."""
    state_typename = kwargs["type"].definition().sections()["DefaultState"].contents()
    state_label = "Usuario::lego visualnoobs::1.0"
    state_cat = hou.sopNodeTypeCategory()

    template = hou.ViewerStateTemplate(state_typename, state_label, state_cat)
    template.bindFactory(State)
    template.bindIcon(kwargs["type"].icon())