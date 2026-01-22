#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extracted_apis.md를 구분별 JSON 파일로 변환

이미 추출된 Markdown 형식의 API 데이터를 JSON으로 변환합니다.

사용법:
    python -m mcp_kr_legislation.utils.api_md_to_json [input_file]
    
    기본 입력: skills/api-integration/extracted_apis.md
    출력: src/mcp_kr_legislation/utils/api_layout/*.json
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any


# 출력 디렉토리
OUTPUT_DIR = Path(__file__).parent / "api_layout"

# 모바일 API 제외
EXCLUDED_CATEGORIES = ["모바일"]

# 구분명 -> 영문 파일명 매핑
CATEGORY_FILE_MAP = {
    "법령": "law",
    "행정규칙": "admin_rule",
    "자치법규": "local_ordinance",
    "연계": "linkage",
    "판례": "precedent",
    "위원회 결정문": "committee",
    "위원회결정문": "committee",
    "조약": "treaty",
    "별표·서식": "appendix",
    "학칙·공단·공공기관": "school_corp",
    "법령용어": "legal_term",
    "맞춤형": "custom",
    "법령정보 지식베이스": "knowledge_base",
    "법령 간 관계": "law_relation",
    "지능형 법령검색 시스템": "intelligent_search",
    "중앙부처해석": "ministry_interpretation",
    "중앙부처 1차 해석": "ministry_interpretation_1",
    "중앙부처 2차 해석": "ministry_interpretation_2",
    "특별행정심판": "special_tribunal",
}


@dataclass
class Parameter:
    """요청 파라미터"""
    name: str
    type: str
    description: str


@dataclass
class SampleUrl:
    """샘플 URL"""
    format: str
    url: str


@dataclass
class ApiInfo:
    """API 정보"""
    id: str
    title: str
    request_url: str
    target: str
    api_type: str
    parameters: List[Parameter] = field(default_factory=list)
    sample_urls: List[SampleUrl] = field(default_factory=list)


def parse_markdown_file(filepath: Path) -> Dict[str, List[ApiInfo]]:
    """
    Markdown 파일 파싱
    
    Returns:
        Dict[카테고리 영문명, List[ApiInfo]]
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    results: Dict[str, List[ApiInfo]] = {}
    
    # 카테고리 섹션 분리 (## N. 카테고리명)
    category_pattern = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)
    category_matches = list(category_pattern.finditer(content))
    
    for i, match in enumerate(category_matches):
        cat_num = match.group(1)
        cat_name = match.group(2).strip()
        
        # 모바일 제외
        if any(exc in cat_name for exc in EXCLUDED_CATEGORIES):
            print(f"  제외: {cat_num}. {cat_name}")
            continue
        
        # 카테고리 섹션 범위 결정
        start = match.end()
        end = category_matches[i + 1].start() if i + 1 < len(category_matches) else len(content)
        section = content[start:end]
        
        # 카테고리 영문명 결정
        # 이름에서 "API" 제거하고 매핑
        cat_name_clean = cat_name.replace(" API", "").strip()
        category_en = CATEGORY_FILE_MAP.get(cat_name_clean, 
                                            cat_name_clean.lower().replace(" ", "_"))
        
        if category_en not in results:
            results[category_en] = []
        
        # API 섹션 파싱 (### N.M API명)
        api_pattern = re.compile(r"^### (\d+\.\d+) (.+)$", re.MULTILINE)
        api_matches = list(api_pattern.finditer(section))
        
        for j, api_match in enumerate(api_matches):
            api_id = api_match.group(1)
            api_title = api_match.group(2).strip()
            
            # API 섹션 범위
            api_start = api_match.end()
            api_end = api_matches[j + 1].start() if j + 1 < len(api_matches) else len(section)
            api_section = section[api_start:api_end]
            
            # API 정보 추출
            api_info = parse_api_section(api_id, api_title, api_section)
            if api_info:
                results[category_en].append(api_info)
    
    return results


def parse_api_section(api_id: str, title: str, section: str) -> Optional[ApiInfo]:
    """API 섹션 파싱"""
    # 요청 URL 추출
    url_match = re.search(r"\*\*요청 URL\*\*[:\s]*`([^`]+)`", section)
    request_url = url_match.group(1) if url_match else ""
    
    # target 추출
    target_match = re.search(r"\*\*target\*\*[:\s]*`([^`]+)`", section)
    target = target_match.group(1) if target_match else ""
    
    # target이 없으면 URL에서 추출
    if not target and request_url:
        target_from_url = re.search(r"target=([a-zA-Z0-9]+)", request_url)
        target = target_from_url.group(1) if target_from_url else ""
    
    # API 타입 결정
    if "본문" in title or "lawService" in request_url:
        api_type = "본문조회"
    else:
        api_type = "목록조회"
    
    # 파라미터 테이블 파싱
    parameters = parse_parameter_table(section)
    
    # 샘플 URL 파싱
    sample_urls = parse_sample_urls(section)
    
    return ApiInfo(
        id=api_id,
        title=title,
        request_url=request_url,
        target=target,
        api_type=api_type,
        parameters=parameters,
        sample_urls=sample_urls
    )


def parse_parameter_table(section: str) -> List[Parameter]:
    """파라미터 테이블 파싱"""
    parameters = []
    
    # 테이블 형식: | 파라미터 | 값 | 설명 |
    table_pattern = re.compile(
        r"\|\s*(\w+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|",
        re.MULTILINE
    )
    
    # 헤더 라인 스킵을 위해 "---" 이후만 파싱
    table_start = section.find("|---")
    if table_start == -1:
        return parameters
    
    table_section = section[table_start:]
    
    for match in table_pattern.finditer(table_section):
        name = match.group(1).strip()
        param_type = match.group(2).strip()
        desc = match.group(3).strip()
        
        # 헤더 행 스킵
        if name in ("파라미터", "---", "요청변수"):
            continue
        
        # 구분선 스킵
        if "-" * 3 in name:
            continue
        
        parameters.append(Parameter(
            name=name,
            type=param_type,
            description=desc
        ))
    
    return parameters


def parse_sample_urls(section: str) -> List[SampleUrl]:
    """샘플 URL 파싱"""
    samples = []
    
    # 샘플 URL 섹션 찾기
    sample_section_match = re.search(r"\*\*샘플 URL\*\*[:\s]*([\s\S]*?)(?=\n###|\n##|\Z)", section)
    if not sample_section_match:
        return samples
    
    sample_section = sample_section_match.group(1)
    
    # 리스트 형식: - XML: `http://...`
    list_pattern = re.compile(r"-\s*(\w+)[:\s]*`([^`]+)`")
    
    for match in list_pattern.finditer(sample_section):
        fmt = match.group(1).upper()
        url = match.group(2)
        
        # 포맷 정규화
        if fmt not in ("XML", "JSON", "HTML"):
            if "XML" in fmt.upper():
                fmt = "XML"
            elif "JSON" in fmt.upper():
                fmt = "JSON"
            elif "HTML" in fmt.upper():
                fmt = "HTML"
            else:
                fmt = "기타"
        
        samples.append(SampleUrl(format=fmt, url=url))
    
    return samples


def save_category_json(category_en: str, apis: List[ApiInfo], 
                       category_name: str, output_dir: Path) -> Path:
    """JSON 파일 저장"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / f"{category_en}.json"
    
    data = {
        "category": category_name,
        "category_en": category_en,
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "api_count": len(apis),
        "apis": [
            {
                "id": api.id,
                "title": api.title,
                "request_url": api.request_url,
                "target": api.target,
                "api_type": api.api_type,
                "parameters": [
                    {"name": p.name, "type": p.type, "description": p.description}
                    for p in api.parameters
                ],
                "sample_urls": [
                    {"format": s.format, "url": s.url}
                    for s in api.sample_urls
                ]
            }
            for api in apis
        ]
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath


# 역매핑: 영문명 -> 한글명
CATEGORY_NAME_MAP = {v: k for k, v in CATEGORY_FILE_MAP.items()}


def main(input_file: Optional[str] = None) -> int:
    """메인 함수"""
    # 입력 파일 결정
    if input_file:
        input_path = Path(input_file)
    else:
        # 기본 경로: 프로젝트 루트의 skills/api-integration/extracted_apis.md
        project_root = Path(__file__).parent.parent.parent.parent
        input_path = project_root / "skills" / "api-integration" / "extracted_apis.md"
    
    if not input_path.exists():
        print(f"입력 파일 없음: {input_path}")
        return 1
    
    print("=" * 60)
    print("extracted_apis.md -> JSON 변환")
    print("=" * 60)
    print(f"입력: {input_path}")
    print(f"출력: {OUTPUT_DIR}")
    print()
    
    # 파싱
    print("[1/2] Markdown 파싱...")
    results = parse_markdown_file(input_path)
    
    total_apis = sum(len(apis) for apis in results.values())
    print(f"  - 카테고리 수: {len(results)}")
    print(f"  - 총 API 수: {total_apis}")
    
    # JSON 저장
    print("\n[2/2] JSON 파일 저장...")
    for category_en, apis in results.items():
        if apis:
            # 한글 카테고리명 결정
            category_name = CATEGORY_NAME_MAP.get(category_en, category_en)
            
            filepath = save_category_json(category_en, apis, category_name, OUTPUT_DIR)
            print(f"  - {filepath.name}: {len(apis)}개 API")
    
    print(f"\n완료: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else None
    raise SystemExit(main(input_file))
