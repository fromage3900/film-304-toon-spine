"""Inspect FBX objects without constructing its potentially polluted rig."""
import json
import sys
from pathlib import Path
from io_scene_fbx import parse_fbx

def text(value):
    return value.decode('utf-8','replace').split('\x00')[0] if isinstance(value,bytes) else value

def child(node,name):
    return next((c for c in node.elems if c.id == name),None)

def prop(node,name):
    p = child(node,b'Properties70')
    if p:
        for item in p.elems:
            if item.id == b'P' and text(item.props[0]) == name:
                return [text(v) for v in item.props[4:]]
    return None

reports=[]
for filename in sys.argv[sys.argv.index('--')+1:]:
    root,version=parse_fbx.parse(filename)
    objects=child(root,b'Objects').elems
    byid={int(o.props[0]):o for o in objects if o.props}
    connections=child(root,b'Connections').elems
    parents={}
    for con in connections:
        if len(con.props)>=3 and con.props[0]==b'OO':
            parents.setdefault(int(con.props[1]),[]).append(int(con.props[2]))
    models=[o for o in objects if o.id==b'Model']
    material_ids={int(o.props[0]):text(o.props[1]) for o in objects if o.id==b'Material'}
    skin_groups={}
    for cluster in (o for o in objects if o.id==b'Deformer' and o.props[-1]==b'Cluster'):
        indexes=child(cluster,b'Indexes')
        weights=child(cluster,b'Weights')
        if indexes is None or weights is None:
            continue
        weighted_ids=set(int(i) for i,w in zip(indexes.props[0],weights.props[0]) if w>.00001)
        bone_names=[text(byid[int(c.props[1])].props[1]) for c in connections if len(c.props)>=3 and c.props[0]==b'OO' and int(c.props[2])==int(cluster.props[0]) and int(c.props[1]) in byid and byid[int(c.props[1])].id==b'Model']
        for skin_id in parents.get(int(cluster.props[0]),[]):
            for geometry_id in parents.get(skin_id,[]):
                if geometry_id in byid and byid[geometry_id].id==b'Geometry':
                    skin_groups.setdefault(geometry_id,[]).append((bone_names,weighted_ids))
    rows=[]
    for geo in (o for o in objects if o.id==b'Geometry' and o.props[-1]==b'Mesh'):
        vertices=child(geo,b'Vertices').props[0]
        indices=child(geo,b'PolygonVertexIndex').props[0]
        model=next((byid[i] for i in parents.get(int(geo.props[0]),[]) if i in byid and byid[i].id==b'Model'),None)
        material_names=[material_ids[int(c.props[1])] for c in connections if len(c.props)>=3 and c.props[0]==b'OO' and model is not None and int(c.props[2])==int(model.props[0]) and int(c.props[1]) in material_ids]
        layer=child(geo,b'LayerElementMaterial')
        mat_ids=child(layer,b'Materials').props[0] if layer and child(layer,b'Materials') else [0]
        parts={}
        polygon=[]
        pindex=0
        for idx in indices:
            polygon.append(int(idx) if idx>=0 else -int(idx)-1)
            if idx<0:
                mid=int(mat_ids[pindex] if len(mat_ids)>1 else mat_ids[0])
                part=parts.setdefault(mid,{'triangles':0,'vertices':set()})
                part['triangles']+=len(polygon)-2
                part['vertices'].update(polygon)
                polygon=[]
                pindex+=1
        for mid,part in parts.items():
            ids=part.pop('vertices')
            part['vertex_count']=len(ids)
            part['bounds']=[[min(vertices[i*3+k] for i in ids),max(vertices[i*3+k] for i in ids)] for k in range(3)]
            part['material']=material_names[mid] if mid<len(material_names) else str(mid)
            part['skin_influences']=[{'bones':names,'vertex_count':len(ids.intersection(weighted))} for names,weighted in skin_groups.get(int(geo.props[0]),[]) if ids.intersection(weighted)]
        ancestors=[]
        current=model
        while current is not None:
            ancestors.append({'name':text(current.props[1]),'visibility':prop(current,'Visibility')})
            current=next((byid[i] for i in parents.get(int(current.props[0]),[]) if i in byid and byid[i].id==b'Model'),None)
        rows.append({'name':text(geo.props[1]),'model':text(model.props[1]) if model else None,'vertices':len(vertices)//3,'triangles':sum(p['triangles'] for p in parts.values()),'parts':parts,'ancestry':ancestors})
    reports.append({'file':filename,'version':version,'limb_nodes':sum(o.props[-1]==b'LimbNode' for o in models),'geometry':rows})
out=Path('G:/film-304-toon-spine/Saved/Audit/dana_fbx_raw_anatomy.json')
out.write_text(json.dumps(reports,indent=2),encoding='utf-8')
print('RAW_FBX_AUDIT',[(r['file'],r['limb_nodes'],len(r['geometry']),sum(g['triangles'] for g in r['geometry'])) for r in reports])
