# AI Ops MVP Frontend

Next.js(App Router) 기반 대시보드 프론트엔드입니다.

## 구현 상태
- [x] Dashboard 기본 화면
  - KPI 카드 4개
  - 재고 테이블(최신순)
  - 재고 위험 위젯(품절/품절 임박)
- [x] 발주 목록/상세/입고 처리 UI
- [x] AI 질의 패널 연동

## 실행 방법
```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:3000` 접속.

## API 연동 환경변수
백엔드 주소를 바꾸려면 아래 중 하나를 설정하세요.

- `NEXT_PUBLIC_API_BASE_URL`
- `API_BASE_URL`

예시:
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api npm run dev
```

설정이 없으면 기본값 `http://localhost:8000/api`를 사용합니다.

## 품질 체크
```bash
npm run lint
npm run build
```

## 유지보수 메모
- API 호출 로직/타입은 `src/lib/api.ts`에 모아 관리합니다.
- 대시보드 화면은 `src/app/page.tsx`에서 서버 컴포넌트로 렌더링합니다.
- 스타일은 `src/app/page.module.css` 단일 모듈로 관리합니다.
