# 포돌이와 친구들

끝없이 이어지는 산과 숲을 곰둥이·포돌이·토실이·란오리가 함께 걸어 다니는 브라우저 오픈월드 데모. 무료 도구만 썼습니다.

- 지형·숲·하늘·물: Three.js로 절차 생성 (청크 스트리밍, LOD, 인스턴싱)
- 캐릭터: 참고 그림 → 이미지→3D 모양 생성 → 그림 투영 텍스처 → Blender 스크립트로 뼈대 자동 삽입 (`refs/blender_rig.py`)
  - 포돌이: Microsoft TRELLIS.2-4B (MIT)
  - 곰둥이·토실이·란오리: Hunyuan3D 2(텐센트) 생성본 — 라이선스 지역 제한(한국 제외) 때문에 MIT 모델(TRELLIS.2)로 교체 진행 중
- 알프스 마을: `refs/alps_assets.py`(블렌더)로 만든 샬레·교회·울타리·물레방아·버섯집·소·양
- 지형 텍스처·하늘: Poly Haven CC0 (`textures/LICENSE.txt`)
- 놀이: 꿀단지 12개 모으기. 소리: 웹오디오 합성(외부 음원 없음)
- 조작: WASD 이동, Shift 달리기, Space 점프, F 비행, V 시점, Q 품질, M 소리

파일 하나(`index.html`)와 모델 네 개(`models/`)로 동작합니다.
