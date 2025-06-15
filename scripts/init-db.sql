-- 웹 호스팅 서비스 데이터베이스 초기화 스크립트
-- PostgreSQL 14+ 지원

-- 데이터베이스 및 사용자 생성 (이미 docker-compose에서 처리됨)
-- CREATE DATABASE webhoster_db;
-- CREATE USER webhoster_user WITH PASSWORD 'webhoster_pass';
-- GRANT ALL PRIVILEGES ON DATABASE webhoster_db TO webhoster_user;

-- 스키마 생성 (기본 public 스키마 사용)
-- CREATE SCHEMA IF NOT EXISTS webhoster;

-- 확장 기능 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 테이블 생성 전에 기존 테이블 정리 (개발 환경용)
-- DROP TABLE IF EXISTS hosting CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- 사용자 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 이메일 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- 호스팅 테이블 생성
CREATE TABLE IF NOT EXISTS hosting (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vm_id VARCHAR(100) UNIQUE NOT NULL,
    vm_ip VARCHAR(45), -- IPv4/IPv6 지원
    ssh_port INTEGER,
    status VARCHAR(50) DEFAULT 'creating',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 호스팅 테이블 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_hosting_user_id ON hosting(user_id);
CREATE INDEX IF NOT EXISTS idx_hosting_vm_id ON hosting(vm_id);
CREATE INDEX IF NOT EXISTS idx_hosting_status ON hosting(status);
CREATE INDEX IF NOT EXISTS idx_hosting_ssh_port ON hosting(ssh_port);

-- 상태 값 제약 조건 추가 (PostgreSQL 14 호환)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_hosting_status'
    ) THEN
        ALTER TABLE hosting 
        ADD CONSTRAINT chk_hosting_status 
        CHECK (status IN ('creating', 'running', 'stopping', 'stopped', 'error'));
    END IF;
END $$;

-- SSH 포트 범위 제약 조건 (PostgreSQL 14 호환)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_hosting_ssh_port'
    ) THEN
        ALTER TABLE hosting 
        ADD CONSTRAINT chk_hosting_ssh_port 
        CHECK (ssh_port >= 10000 AND ssh_port <= 20000);
    END IF;
END $$;

-- 테이블 업데이트 트리거 함수 생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_hosting_updated_at ON hosting;
CREATE TRIGGER update_hosting_updated_at
    BEFORE UPDATE ON hosting
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 테스트 데이터 생성 (개발 환경용)
-- 비밀번호: "testpass123" (bcrypt 해시)
INSERT INTO users (email, hashed_password, username, is_active) 
VALUES (
    'test@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeKsWhlhKJfUfqt3q',
    'testuser',
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- 권한 부여 (추가 보안)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO webhoster_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO webhoster_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO webhoster_user;

-- 기본 권한 설정
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO webhoster_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO webhoster_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO webhoster_user;

-- 연결 제한 설정 (선택사항)
-- ALTER USER webhoster_user CONNECTION LIMIT 20;

-- 데이터베이스 통계 업데이트
ANALYZE users;
ANALYZE hosting;

-- 초기화 완료 로그
DO $$
BEGIN
    RAISE NOTICE '웹 호스팅 서비스 데이터베이스 초기화 완료';
END $$; 