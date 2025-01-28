import ifcopenshell

def process_ifc_to_graph(ifc_file_path, max_nodes=50000, max_relationships=50000):
    """
    Process an IFC file and convert it to a graph-compatible JSON for Cytoscape.
    Limits the number of nodes and relationships to the specified maximum values.

    Args:
        ifc_file_path (str): Path to the IFC file.
        max_nodes (int): Maximum number of nodes to process.
        max_relationships (int): Maximum number of relationships to process.
    """
    ifc_file = ifcopenshell.open(ifc_file_path)
    entities = sorted(ifc_file, key=lambda e: e.id())

    total_entities = len(entities)
    if total_entities > max_nodes:
        print(f"Input file contains {total_entities} entities. Limiting to {max_nodes} nodes.")
        entities = entities[:max_nodes]
    else:
        print(f"Processing all {total_entities} entities.")

    graph = {"nodes": [], "edges": []}
    relationship_count = 0

    for entity in entities:
        if len(graph["nodes"]) >= max_nodes:
            break  # Stop adding nodes if the limit is reached

        entity_id = entity.id()
        entity_type = entity.is_a()
        attributes = entity.get_info()

        # Add node
        graph["nodes"].append({
            "data": {
                "id": str(entity_id),
                "label": entity_type,
                **{k: v for k, v in attributes.items() if isinstance(v, (str, int, float, bool))}
            }
        })

        # Add relationships (limit to max_relationships)
        for rel_name, rel_value in attributes.items():
            if relationship_count >= max_relationships:
                break

            if isinstance(rel_value, ifcopenshell.entity_instance):
                graph["edges"].append({
                    "data": {
                        "source": str(entity_id),
                        "target": str(rel_value.id()),
                        "label": rel_name
                    }
                })
                relationship_count += 1
            elif isinstance(rel_value, list) and all(isinstance(r, ifcopenshell.entity_instance) for r in rel_value):
                for related_entity in rel_value:
                    if relationship_count >= max_relationships:
                        break
                    graph["edges"].append({
                        "data": {
                            "source": str(entity_id),
                            "target": str(related_entity.id()),
                            "label": rel_name
                        }
                    })
                    relationship_count += 1

    print(f"Graph created with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges.")
    return graph
