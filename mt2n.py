import re
import os
import json
import copy


class Properties:

    def __init__(self, file_name):
        self.properties = dict()
        self.read_properties_file(file_name)

    def read_properties_file(self, file_name):
        try:
            prop_file = open(file_name, 'r', encoding='utf-8')
            for line in prop_file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    continue
                strs = re.split(r"\s=\s", line, 1)
                self.properties[strs[0]] = strs[1]
        except Exception as e:
            raise e
        else:
            prop_file.close()

    def read_property(self, param):
        return self.properties[param]

    def read_list(self, param):
        res = list()
        with open(self.properties[param], "r") as file:
            for line in file.readlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    continue
                res.append(line)
        return res

    def read_dict(self, param):
        res = dict()
        with open(self.properties[param], "r") as file:
            for line in file.readlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    continue
                strs = line.split("\t")
                res[strs[0]] = strs[1]
        return res


class DiGraph:

    def __init__(self, property_path):
        os.chdir(os.path.dirname(__file__))
        self.properties = Properties(property_path)
        self.identifiers = self.properties.read_dict("mt2n.identifiersPath")

        self.graph = {"Vertices": [], "Edges": []}
        self.exist_entities = dict()  # {entity_type: {identifier_value: id}}
        self.node_count = 0
        self.exist_edges = dict()  # {source_id: set of target_id}
        self.id_mapping = dict()  # {raw_id: new_id}
        self.entity_type_to_id = dict()  # {entity_type: id}
        self.id_to_entity_type = dict()  # {id: entity_type}
        self.entity_type_count = 0
        self.relationship_type_to_id = dict()  # {relationship_type: id}
        self.id_to_relationship_type = dict()  # {relationship_type: id}
        self.relationship_type_count = 0

    def check_node_exists(self, entity_type, properties):
        if entity_type not in self.exist_entities.keys():
            self.exist_entities[entity_type] = dict()
        if self.id_to_entity_type[entity_type] in self.identifiers.keys():
            tmp = properties[self.identifiers[self.id_to_entity_type[entity_type]]]
            if tmp in self.exist_entities[entity_type].keys():
                return self.exist_entities[entity_type][tmp]  # return id
        return -1

    def add_node(self, raw_id, entity_type, properties):
        is_existing = self.check_node_exists(entity_type, properties)
        if is_existing == -1:
            self.graph["Vertices"].append({"id": self.node_count, "entity_type": entity_type, "properties": properties})
            self.id_mapping[raw_id] = self.node_count
            if self.id_to_entity_type[entity_type] in self.identifiers.keys():
                tmp = properties[self.identifiers[self.id_to_entity_type[entity_type]]]
                self.exist_entities[entity_type][tmp] = self.node_count
            self.node_count += 1
        else:
            self.id_mapping[raw_id] = self.node_count
            for k, v in properties.items():
                if k not in self.graph["Vertices"][is_existing]["properties"].keys():
                    self.graph["Vertices"][is_existing]["properties"][k] = v

    def add_edge(self, source_raw_id, target_raw_id, relationship_type):
        source_id = self.id_mapping[source_raw_id]
        target_id = self.id_mapping[target_raw_id]
        if source_id not in self.exist_edges.keys():
            self.exist_edges[source_id] = set()
        if target_id not in self.exist_edges[source_id]:
            self.exist_edges[source_id].add(target_id)
            self.graph["Edges"].append({"source_id": source_id, "target_id": target_id, "relationship": relationship_type})

    def merge_ttl(self):
        ttl_path = self.properties.read_list("mt2n.ttlPath")
        for path in ttl_path:
            with open(path, "r") as file:
                entities_tmp = dict()
                edges_tmp = list()
                for line in file.readlines():
                    line = line.strip()
                    if line:
                        # read one line of ttl file
                        line = line.split(" ", 2)
                        line[2] = line[2][:-2]
                        if line[2][0] == '_':
                            # read edges
                            source = line[0]
                            target = line[2]
                            relationship = line[1]
                            if relationship not in self.relationship_type_to_id.keys():
                                self.relationship_type_to_id[relationship] = self.relationship_type_count
                                self.id_to_relationship_type[self.relationship_type_count] = relationship
                                relationship = self.relationship_type_count
                                self.relationship_type_count += 1
                            else:
                                relationship = self.relationship_type_to_id[relationship]
                            edges_tmp.append((source, target, relationship))
                        else:
                            # read nodes
                            rdf_id = line[0]
                            if line[2].startswith("<"):
                                entity_type = line[2]
                                if entity_type not in self.entity_type_to_id.keys():
                                    self.entity_type_to_id[entity_type] = self.entity_type_count
                                    self.id_to_entity_type[self.entity_type_count] = entity_type
                                    entity_type = self.entity_type_count
                                    self.entity_type_count += 1
                                else:
                                    entity_type = self.entity_type_to_id[entity_type]
                                if rdf_id not in entities_tmp.keys():
                                    entities_tmp[rdf_id] = {"entity_type": entity_type, "properties": {}}
                                else:
                                    entities_tmp[rdf_id]["entity_type"] = entity_type
                            else:
                                data_type = line[1]
                                data = line[2][1:-1]
                                if rdf_id not in entities_tmp.keys():
                                    entities_tmp[rdf_id] = {"properties": {data_type: data}}
                                else:
                                    entities_tmp[rdf_id]["properties"][data_type] = data
                    else:
                        for rdf_id, info in entities_tmp.items():
                            self.add_node(rdf_id, info["entity_type"], info["properties"])
                        for source, target, relationship in edges_tmp:
                            self.add_edge(source, target, relationship)
                        entities_tmp = dict()
                        edges_tmp = list()

    def dump_json(self):
        output_path = self.properties.read_property("mt2n.outputJsonPath")
        with open(output_path, "w") as file:
            json.dump(self.graph, file, ensure_ascii=False, indent=4)

    def dump_csv_for_gephi(self):
        node_path = self.properties.read_property("mt2n.outputCsvNodePath")
        edge_path = self.properties.read_property("mt2n.outputCsvEdgePath")
        node_path = open(node_path, 'w')
        edge_path = open(edge_path, 'w')
        node_path.write('Id,Label,Polygon\n')
        edge_path.write('Source,Target,Type,Label,Weight\n')

        tmp_node_count = self.node_count
        for edge in self.graph["Edges"]:
            edge_path.write("{},{},{},\"{}\",{}\n".format(edge["source_id"], edge["target_id"], "Directed", self.id_to_relationship_type[edge["relationship"]], 1))
        for vertex in self.graph["Vertices"]:
            node_path.write("{},\"{}\",{}\n".format(vertex["id"], self.id_to_entity_type[vertex["entity_type"]], 0))
            for k, v in vertex["properties"].items():
                node_path.write("{},\"{}\",{}\n".format(tmp_node_count, v, 3))
                edge_path.write("{},{},{},\"{}\",{}\n".format(vertex["id"], tmp_node_count, "Undirected", k, 1))
                tmp_node_count += 1
        node_path.close()
        edge_path.close()

    def output_mapping(self):
        entity_path = self.properties.read_property("mt2n.outputEntityPath")
        with open(entity_path, "w") as file:
            for k, v in self.entity_type_to_id.items():
                file.write("{}\t{}\n".format(v, k))
        relationship_path = self.properties.read_property("mt2n.outputRelationshipPath")
        with open(relationship_path, "w") as file:
            for k, v in self.relationship_type_to_id.items():
                file.write("{}\t{}\n".format(v, k))

    def dump(self):
        self.dump_json()
        self.dump_csv_for_gephi()
        self.output_mapping()


if __name__ == "__main__":
    g = DiGraph("PathProperty.properties")
    g.merge_ttl()

