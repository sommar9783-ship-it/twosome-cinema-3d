이 폴더에 GLB 파일을 아래 이름으로 넣으면, 게임이 시작할 때 자동으로 해당 부분을 그 모델로 교체합니다.
파일을 빼면(예: unused 폴더로 옮기면) 그 부분만 예전 방식으로 돌아갑니다.

  kiosk.glb    티켓 발권기 2대          (뷰 3장 → Tripo H3.1 멀티뷰, 30만 폴리곤)
  claw.glb     인형뽑기 (안이 빈 기계)   (claw_empty.png → Tripo 단일 이미지)
  grab.glb     인형뽑기 집게 머리        (claw_part_c.png)
  booth.glb    포토부스 겉모습           (촬영하러 들어가면 입구가 뚫린 안쪽 세트로 자동 전환)
  loc.glb      상영관 입구의 극장 외관
  door.glb     뒷벽 출입문
  cafe.glb     카페 카운터               (cafe.png)
  cake_a/b/c.glb  케이크 3종 + 받침대     (cake_a/b/c.png)
  seat.glb     상영관 좌석 84개 (저폴리 버전을 한 번에 그림. 로비 벽 앞 의자는 없앰)
  plant.glb    화분 2개
  table.glb    사이드 테이블
  berry.glb    낱개 딸기 (바닥·손·카페·으깨기)
  char.glb     캐릭터 (모든 캐릭터 공통, Meshy 7 리깅 모델. 뼈대를 게임이 직접 움직여 걷기·앉기·만세를 만듦)
               원본은 original/char_rig.glb, 이전 통짜 인형은 unused/char_static.glb

  original/    경량화하기 전 원본 (힉스필드에서 받은 그대로). 이 폴더의 파일을 위로 복사하면 그 모델만 원본으로 돌아감
               경량화: npx @gltf-transform/cli weld → simplify --ratio 0.1~0.3 --error 0.02 → resize 1024~2048
               (전체 123MB → 35MB, 화면 폴리곤 약 390만 → 88만)
  unused/      쓰지 않는 이전 버전 보관 (kiosk_1440k = 144만 폴리곤 키오스크, claw_filled = 인형이 들어찬 인형뽑기)

벽지·바닥은 assets/textures 의 wall1.jpg, floor.jpg 입니다. 같은 이름으로 바꿔 넣으면 교체됩니다.
(wall1.jpg 는 "기둥+패널+액자" 한 칸을 잘라 벽 전체에 반복하고, 액자 안에 포스터·메뉴·그림을 넣습니다.)

2026-11-12 변경: 표면이 울퉁불퉁하던 Tripo 모델을 Hunyuan3D v3 모델로 교체
- Hunyuan 사용: kiosk, door, booth, loc, cafe, table, cake_a/b/c  (원본은 original/<이름>_hunyuan.glb, 이전 Tripo 판은 unused/<이름>_tripo.glb)
- 인형뽑기(claw)와 상영관 좌석은 AI 모델을 쓰지 않고 게임 코드가 반듯한 도형으로 직접 만듭니다.
  (Hunyuan 인형뽑기는 유리창이 막힌 통짜로 나와 안의 집게·인형이 안 보여서 unused/claw_hunyuan_closed.glb 로 보관)
- 다시 뽑을 때:  higgsfield generate create hunyuan3d_v3_image_to_3d --image X_f.png [--image X_s.png --image X_b.png] --face_count 150000 --wait
  뷰 1장 15크레딧, 3장 19크레딧 (--enable_pbr true 를 붙이면 19 / 23크레딧. 게임은 그 재질 지도를 쓰지 않음)
- 모델 정면: Hunyuan 은 대체로 0도, 뒷문만 -90도 (index.html 의 HY / MODEL_YAW)

2026-11-12 (이후) 변경: AI 모델이 계속 찌글거려서, 블렌더(5.3)로 직접 만든 모델로 교체
- loc.glb(극장 외관) · claw.glb(인형뽑기) · door.glb(뒷문): tools/build_models.py 가 반듯한 도형 + 둥근 모서리 + 입체 글자로 만듦
  다시 만들기:  "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b -P tools/build_models.py -- assets/models
  (색·크기·글자를 바꾸려면 그 스크립트의 숫자/문구를 고치면 됨)
- char.glb(캐릭터): 뷰 3장으로 만든 메시(original/char.glb)에 tools/rig_char.py 로 뼈대를 직접 심음. 목 위(얼굴+모자)는 통째로 움직여 찌그러지지 않음
  다시 만들기:  blender -b -P tools/rig_char.py -- assets/models/original/char.glb assets/models/char.glb
- 이전 판은 unused/ 에 보관 (loc_hunyuan_opt, door_hunyuan_opt, char_meshy_rig 등)

규칙
- 크기·바닥·중심은 게임이 자동으로 맞춥니다.
- 정면 방향은 index.html 의 MODEL_YAW 에서 맞춥니다. Tripo 결과물은 모두 -90도(-Math.PI/2)였습니다.

힉스필드 CLI로 다시 뽑을 때 (개당 9크레딧, 원본 이미지는 assets/views)
  뷰 3장:  higgsfield generate create tripo_h3_1_multiview_to_3d --image X_f.png --image X_s.png --image X_b.png --face_limit 300000 --wait
  뷰 1장:  higgsfield generate create tripo_h3_1_image_to_3d --image X.png --face_limit 80000 --wait
- geometry_quality / texture_quality 를 detailed 로 올리면(18크레딧) 2026-11-12 에 5건 모두 실패(환불)했습니다.
- 팔다리가 움직이는 캐릭터는 Meshy 7 리깅(meshy_v7_image_to_3d --enable_rigging true, 견적 44크레딧)이 필요합니다.

==== 2026-11-13 갱신 ====
- char.glb      : 힉스필드 Meshy 7 로 새로 생성(리깅 + 'Casual_Walk' 걷기 모션 포함, 약 3만 폴리곤). 게임이 걷기 클립을 그대로 재생하고,
                  앉기·물건 들기·만세만 코드로 덧씌움. 원본은 original/char_meshy_walk.glb, 이전 것은 unused/char_blender_rig.glb
- staff.glb     : 매표 창구 직원(벨보이). Seedream 5.5 이미지 → Hunyuan 3D. 원본은 original/staff_hunyuan.glb
- kiosk.glb     : 화면을 수직으로 바꿔 게임 화면과 정확히 맞춤 (tools/build_props.py)
- claw.glb      : 유리 바닥 겹침(줄무늬) 수정
- textures/m_ceiling.jpg : 천장(우물천장) 텍스처, Seedream 5.5
- 금색/크롬 등은 텍스처 대신 index.html 의 BL_PBR 값(색·금속성·거칠기)으로 지정
