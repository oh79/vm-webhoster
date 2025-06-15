# 성능 최적화 가이드

## 🚀 즉시 적용 가능한 최적화 방법

### 1. 프로덕션 모드로 실행
```bash
# 개발 모드 (느림)
npm run dev

# 프로덕션 빌드 후 실행 (빠름)
npm run build
npm run start
```

### 2. 번들 크기 분석
```bash
npm run analyze
```

### 3. 컴포넌트 최적화
- React.memo() 사용으로 불필요한 리렌더링 방지
- useMemo(), useCallback() 적절히 활용
- 동적 import로 코드 스플리팅

### 4. 이미지 최적화
- Next.js Image 컴포넌트 사용
- WebP/AVIF 포맷 활용
- 적절한 크기 조정

### 5. 상태 관리 최적화
- Zustand 스토어 분할
- 불필요한 상태 업데이트 최소화
- 로컬 상태 vs 전역 상태 구분

## 🔧 고급 최적화 방법

### 1. 서버 사이드 렌더링 활용
```tsx
// 정적 생성
export async function getStaticProps() {
  return { props: { data } }
}

// 서버 사이드 렌더링
export async function getServerSideProps() {
  return { props: { data } }
}
```

### 2. API 호출 최적화
```tsx
// SWR 또는 React Query 사용
import useSWR from 'swr'

function Profile() {
  const { data, error } = useSWR('/api/user', fetcher)
  if (error) return <div>로딩 실패</div>
  if (!data) return <div>로딩 중...</div>
  return <div>안녕하세요 {data.name}님!</div>
}
```

### 3. 코드 스플리팅
```tsx
import dynamic from 'next/dynamic'

const DynamicComponent = dynamic(() => import('../components/heavy-component'), {
  loading: () => <p>로딩 중...</p>,
})
```

## 📊 성능 측정 도구

1. **Lighthouse** - 전체적인 성능 점수
2. **React DevTools Profiler** - 컴포넌트 렌더링 성능
3. **Next.js Bundle Analyzer** - 번들 크기 분석
4. **Chrome DevTools** - 네트워크, 메모리 사용량

## ⚡ 즉시 확인 사항

- [ ] 프로덕션 모드로 실행 중인가?
- [ ] 번들 크기가 적절한가? (< 1MB)
- [ ] 이미지 최적화가 활성화되어 있는가?
- [ ] 불필요한 리렌더링이 없는가?
- [ ] API 호출이 최적화되어 있는가? 