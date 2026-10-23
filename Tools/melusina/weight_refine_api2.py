# Tools/melusina/weight_refine_api2.py
# Topology-aware skin weight refinement using Maya API 2.0.
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

def get_mesh_dag_path(mesh_transform):
    sel = om.MSelectionList()
    sel.add(mesh_transform)
    return sel.getDagPath(0)

def get_adjacency(dag_path):
    it = om.MItMeshVertex(dag_path)
    num = it.count()
    adjacency = [[] for _ in range(num)]
    while not it.isDone():
        idx = it.index()
        adjacency[idx] = list(it.getConnectedVertices())
        it.next()
    return adjacency

def get_skin_cluster_fn(skin_cluster_name):
    sel = om.MSelectionList()
    sel.add(skin_cluster_name)
    node = sel.getDependNode(0)
    return oma.MFnSkinCluster(node)

def get_influence_paths(skin_cluster_name):
    from maya import cmds
    names = cmds.skinCluster(skin_cluster_name, q=True, influence=True)
    paths = []
    for n in names:
        sel = om.MSelectionList()
        sel.add(n)
        paths.append(sel.getDagPath(0))
    return paths

def get_all_weights(skin_cluster_name, influence_names, mesh_shape, num_verts):
    from maya import cmds
    cmds.select(mesh_shape)
    flat = cmds.skinCluster(skin_cluster_name, q=True, weight=True)
    if flat is None:
        return [[0.0] * num_verts for _ in range(len(influence_names))]
    num_infl = len(influence_names)
    weights = [[0.0] * num_verts for _ in range(num_infl)]
    for v in range(num_verts):
        base = v * num_infl
        for i in range(num_infl):
            weights[i][v] = float(flat[base + i])
    return weights

def set_all_weights(skin_fn, influence_paths, weights, dag_path):
    num_verts = om.MFnMesh(dag_path).numVertices
    comp_fn = om.MFnSingleIndexedComponent()
    comp = comp_fn.create(om.MFn.kMeshVertComponent)
    comp_fn.addElements(list(range(num_verts)))
    flat = []
    for v in range(num_verts):
        for i in range(len(influence_paths)):
            flat.append(weights[i][v])
    flat_arr = om.MFloatArray(flat)
    influence_array = om.MDagPathArray()
    for p in influence_paths:
        influence_array.append(p)
    skin_fn.setWeights(dag_path, comp, flat_arr, influence_array, False)

def smooth_weights(weights, adjacency, iterations=2):
    num_infl = len(weights)
    if num_infl == 0:
        return weights
    num_verts = len(weights[0])
    for _ in range(iterations):
        new_weights = [[0.0] * num_verts for _ in range(num_infl)]
        for v in range(num_verts):
            neighbors = adjacency[v]
            if not neighbors:
                for i in range(num_infl):
                    new_weights[i][v] = weights[i][v]
                continue
            total = len(neighbors) + 1
            for i in range(num_infl):
                s = weights[i][v]
                for n in neighbors:
                    s += weights[i][n]
                new_weights[i][v] = s / total
        weights = new_weights
    return weights

def normalize_weights(weights):
    num_infl = len(weights)
    if num_infl == 0:
        return weights
    num_verts = len(weights[0])
    for v in range(num_verts):
        total = sum(weights[i][v] for i in range(num_infl))
        if total <= 1e-6:
            continue
        for i in range(num_infl):
            weights[i][v] /= total
    return weights

def repair_zero_weights(weights, adjacency):
    num_infl = len(weights)
    if num_infl == 0:
        return weights, 0
    num_verts = len(weights[0])
    repaired = 0
    for v in range(num_verts):
        total = sum(weights[i][v] for i in range(num_infl))
        if total > 1e-6:
            continue
        acc = [0.0] * num_infl
        count = 0
        for n in adjacency[v]:
            ntotal = sum(weights[i][n] for i in range(num_infl))
            if ntotal > 1e-6:
                for i in range(num_infl):
                    acc[i] += weights[i][n]
                count += 1
        if count > 0:
            for i in range(num_infl):
                weights[i][v] = acc[i] / count
            repaired += 1
    return weights, repaired

def clamp_influences(weights, max_influences):
    num_infl = len(weights)
    if num_infl == 0:
        return weights
    num_verts = len(weights[0])
    for v in range(num_verts):
        pairs = [(weights[i][v], i) for i in range(num_infl)]
        pairs.sort(reverse=True)
        keep = pairs[:max_influences]
        for i in range(num_infl):
            weights[i][v] = 0.0
        total = sum(w for w, i in keep)
        if total <= 1e-6:
            continue
        for w, i in keep:
            weights[i][v] = w / total
    return weights

def prune_small_weights(weights, threshold=0.001):
    num_infl = len(weights)
    if num_infl == 0:
        return weights
    num_verts = len(weights[0])
    for v in range(num_verts):
        for i in range(num_infl):
            if weights[i][v] < threshold:
                weights[i][v] = 0.0
    return weights
