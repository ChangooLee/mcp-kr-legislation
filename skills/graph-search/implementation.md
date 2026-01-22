# 지식 그래프 구현 코드

## 노드 생성

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class LawNode:
    """법령 노드"""
    law_id: str
    law_name: str
    law_type: str  # "법률", "시행령", etc.
    promulgation_date: Optional[str] = None
    enforcement_date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": f"law_{self.law_id}",
            "type": "Law",
            "label": self.law_name,
            "properties": {
                "law_id": self.law_id,
                "law_name": self.law_name,
                "law_type": self.law_type,
                "promulgation_date": self.promulgation_date,
                "enforcement_date": self.enforcement_date,
            }
        }

@dataclass
class PrecedentNode:
    """판례 노드"""
    prec_id: str
    case_name: str
    court: str  # "대법원", "헌법재판소", etc.
    decision_date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": f"prec_{self.prec_id}",
            "type": "Precedent",
            "label": self.case_name,
            "properties": {
                "prec_id": self.prec_id,
                "case_name": self.case_name,
                "court": self.court,
                "decision_date": self.decision_date,
            }
        }
```

## 엣지 생성

```python
@dataclass
class GraphEdge:
    """그래프 엣지"""
    from_id: str
    to_id: str
    relation: str
    weight: float = 1.0
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "relation": self.relation,
            "weight": self.weight,
            "metadata": self.metadata or {}
        }

# 예시: 법령이 다른 법령을 참조
edge = GraphEdge(
    from_id="law_12345",
    to_id="law_67890",
    relation="references",
    weight=1.0,
    metadata={"article": "제1조"}
)
```

## 지식 그래프 빌드

```python
def build_knowledge_graph(
    law_data: Dict[str, Any],
    precedent_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    법령 데이터로부터 지식 그래프 생성
    """
    nodes = []
    edges = []
    
    # 법령 노드 생성
    law_node = LawNode(
        law_id=law_data["법령ID"],
        law_name=law_data["법령명"],
        law_type=law_data.get("법령구분", ""),
        promulgation_date=law_data.get("공포일자"),
        enforcement_date=law_data.get("시행일자")
    )
    nodes.append(law_node.to_dict())
    
    # 판례 노드 생성 (있는 경우)
    if precedent_data:
        prec_node = PrecedentNode(
            prec_id=precedent_data["판례일련번호"],
            case_name=precedent_data["사건명"],
            court="대법원",
            decision_date=precedent_data.get("선고일자")
        )
        nodes.append(prec_node.to_dict())
        
        # 판례-법령 관계 엣지
        edge = GraphEdge(
            from_id=prec_node.to_dict()["id"],
            to_id=law_node.to_dict()["id"],
            relation="interprets",
            metadata={"article": precedent_data.get("관련조문", "")}
        )
        edges.append(edge.to_dict())
    
    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    }
```

## 그래프 저장

```python
def save_knowledge_graph(
    graph_data: Dict[str, Any],
    cache_dir: Path = None
) -> Path:
    """
    지식 그래프를 파일로 저장
    """
    if cache_dir is None:
        cache_dir = Path(__file__).parent.parent / "utils" / "data" / "knowledge_graph"
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # 노드 저장
    with open(cache_dir / "nodes.json", "w", encoding="utf-8") as f:
        json.dump(graph_data["nodes"], f, ensure_ascii=False, indent=2)
    
    # 엣지 저장
    with open(cache_dir / "edges.json", "w", encoding="utf-8") as f:
        json.dump(graph_data["edges"], f, ensure_ascii=False, indent=2)
    
    return cache_dir
```

## 그래프 쿼리

```python
def query_knowledge_graph(
    query: str,
    relation_type: Optional[str] = None,
    node_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    자연어 쿼리로 지식 그래프 검색
    
    예시:
    - "개인정보보호법을 참조하는 법령"
    - "개인정보보호법을 해석한 판례"
    - "개인정보보호위원회 결정문"
    """
    # 그래프 로드
    cache_dir = Path(__file__).parent.parent / "utils" / "data" / "knowledge_graph"
    
    with open(cache_dir / "nodes.json", "r", encoding="utf-8") as f:
        nodes = json.load(f)
    
    with open(cache_dir / "edges.json", "r", encoding="utf-8") as f:
        edges = json.load(f)
    
    # 쿼리 파싱 (간단한 예시)
    results = []
    
    # 노드 검색
    for node in nodes:
        if query.lower() in node["label"].lower():
            results.append(node)
    
    # 관계 검색
    if relation_type:
        for edge in edges:
            if edge["relation"] == relation_type:
                # 관련 노드 찾기
                from_node = next((n for n in nodes if n["id"] == edge["from"]), None)
                to_node = next((n for n in nodes if n["id"] == edge["to"]), None)
                if from_node and to_node:
                    results.append({
                        "from": from_node,
                        "to": to_node,
                        "relation": edge["relation"]
                    })
    
    return results
```
