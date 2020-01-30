import sys
from random import random
import xml.etree.ElementTree as et
from Config import *


class Renderer:

    def __init__(self, amodel, template_path):
        self.template_path = template_path
        self.amodel = amodel
        self.tree = et.parse(template_path)
        self.set_nodes()
        self.set_components()

    def set_nodes(self):
        root = self.tree.getroot()
        nodes = root[0]
        
        for name, vals in self.amodel.nodes.items():
            data = {
                "id": str(vals["id"]),
                "tagname": str(name),
                "x": str(vals["pos"][0]),
                "y": str(vals["pos"][1]),
                "z": str(vals["pos"][2])
            }
            if vals["dof"]:
                dof = {
                    "TranslationX": "true",
                    "TranslationY": "true",
                    "TranslationZ": "true",
                    "rotationX": "true",
                    "rotationY": "true",
                    "rotationZ": "true"
                }
            else:
                dof = {
                    "TranslationX": "false",
                    "TranslationY": "false",
                    "TranslationZ": "false",
                    "rotationX": "true",
                    "rotationY": "true",
                    "rotationZ": "true"
                }
            node = et.SubElement(nodes, "node", data)
            et.SubElement(node, "dof6", dof)
    
    def set_components(self):
        root = self.tree.getroot()
        components = root[2]
        mooring_data = {
            "addedmasscoefflocaly":"0.0",
            "addedmasscoefflocalz":"0.0",
            "areal":"0.0",
            "massdensity":"0.0",
            "noCompressionForces":"false",
            "pretension":"0.0",
            "weightInAir":"0.0",
            "young":"0.0"
        }
        extra_data = {
            "breakingload":"0.0",
            "materialcoefficient":"0.0",
            "trusstype":"3",
            "weighttoaimfor":"0.0"
        }
        loadmodel_data = {
            "LoadType":"MORRISON",
            "closeSurfaceNumPoints":"0",
            "constructionDamping":"0.0",
            "currentreduction":"0.0",
            "dragArealy":"0.0",
            "dragArealyz":"0.0",
            "dragCoeffy":"1.2",
            "dragCoeffz":"1.2",
            "hullnumPoints":"0",
            "massRadius":"0.0",
            "numWaveHeading":"0",
            "numvelocities":"0",
            "rayleighStiffness":"0.0",
            "tangentialDragCoefficient":"0.0",
            "viscousRollDamping":"1.0",
            "wavereduction":"0.0"
        }
        description_data = {"active": "true", "des": ""}
        for name, vals in self.amodel.edges.items():
            truss_data = {"id": str(vals["edge_id"]), "name": str(name)}
            color_data = {
                "blue": str(random()),
                "green": str(random()),
                "red": str(random())
            }
            truss = et.SubElement(components, "truss", truss_data)
            et.SubElement(truss, "mooring", mooring_data)
            et.SubElement(truss, "extra", extra_data)
            et.SubElement(truss, "loadmodel", loadmodel_data)
            description = et.SubElement(truss, "description", description_data)
            et.SubElement(description, "color", color_data)
            if "edge" in vals:
                element_data = {
                    "id": str(vals["edge_id"]),
                    "StartNode_ID": str(self.amodel.nodes[vals["edge"][1]]["id"]),
                    "EndNode_ID": str(self.amodel.nodes[vals["edge"][0]]["id"])
                }
                elements = et.SubElement(truss, "elements")
                et.SubElement(elements, "element", element_data)
    
    def write(self, path):
        self.tree.write(path)


def main():
    config_path = sys.argv[1]
    model_path = sys.argv[2]
    xml_template = "model_template.xml"
    config = Config(config_path)
    rendr = Renderer(config, xml_template)
    rendr.write(model_path)


if __name__ == "__main__":
    main()