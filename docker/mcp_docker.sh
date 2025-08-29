#!/bin/bash

# ------------------------------------------------------------
# 실행 옵션 설정
# ------------------------------------------------------------
set -e

# ------------------------------------------------------------
# 색상 정의
# ------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ------------------------------------------------------------
# 프로젝트 디렉토리 경로 구하기
# ------------------------------------------------------------
# script 디렉토리 경로 구하기
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# project root 디렉토리 경로 구하기
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ------------------------------------------------------------
# 프로젝트 루트로 이동
# ------------------------------------------------------------
cd "${PROJECT_ROOT}"
echo "${PROJECT_ROOT}"

# ------------------------------------------------------------
# 로그 함수
# ------------------------------------------------------------
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}
log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}
log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}
log_success() {
    echo -e "${CYAN}[SUCCESS]${NC} $1"
}
log_debug() {
    echo -e "${MAGENTA}[DEBUG]${NC} $1"
}

# ------------------------------------------------------------
# 서비스/포트 유틸리티
# ------------------------------------------------------------

# 지정 포트의 /health 엔드포인트에서 2xx 상태코드 반환하는 지 확인
is_health_ok() {
    local port="$1"
    curl -f -s "http://localhost:${port}/health" > /dev/null 2>&1
}
# 지정 포트가 사용 중인지 확인
is_port_in_use() {
    local port="$1"
    if command -v lsof > /dev/null 2>&1; then
        lsof -iTCP:"${port}" -sTCP:LISTEN > /dev/null 2>&1
        return $?
    fi
    return 1
}
# 컨테이너가 실행 중인지 확인
is_container_running() {
    local container_name="$1"
    if command -v docker > /dev/null 2>&1; then
        docker ps --format '{{.Names}}' | grep -q "^${container_name}$" > /dev/null 2>&1
        return $?
    fi
    return 1
}
# 특정 서비스를 실행하는 도커 컨테이너가 실행 중이며, 헬시한지 확인
is_docker_service_healthy() {
    local container_name="$1"
    local port="$2"
    if is_container_running "${container_name}" && is_health_ok "${port}"; then
        return 0
    fi
    return 1
}

# ------------------------------------------------------------
# 도움말 표시
# ------------------------------------------------------------
show_help() {
    cat << EOF
MCP Server Docker 관리 스크립트

사용법:
    $0 <command> [options]

명령어:
    build         모든 MCP Server image 빌드
    run           모든 MCP Server 시작 (백그라운드)
    stop          모든 MCP Server 중지
    restart       모든 MCP Server 재시작
    logs          모든 Server Log 확인
    logs <server> 특정 Server Log 확인 (tavily)
    status        Server 상태 확인
    clean         중지된 컨테이너 및 미사용 이미지 정리
    test          모든 Server 헬스체크 테스트

예시:
    $0 build              # 이미지 빌드
    $0 run                # 서버 시작
    $0 logs tavily        # tavily MCP Server 로그만 출력
    $0 test               # 헬스체크 테스트
EOF
}

# ------------------------------------------------------------
# 파일 확인
# ------------------------------------------------------------
# .env 파일 확인
check_env_file() {
    local env_file="${PROJECT_ROOT}/.env"
    local example_file="${PROJECT_ROOT}/env.example"

    if [ ! -f "${env_file}" ]; then
        log_warning "${PROJECT_ROOT}에 .env 파일이 존재하지 않습니다. env.example을 참고하여 생성하세요."
        log_info ".env 파일 경로: ${env_file}"

        if [ -f "${example_file}" ]; then
            log_info "env.example의 내용을 .env로 복사하시겠습니까? (y/N)"
            read -r response

            if [[ "${response}" =~ ^[Yy]$ ]]; then
                cp "${example_file}" "${env_file}"
                log_success ".env 파일을 생성하였습니다. API 키를 설정해주세요."
                log_info ".env 파일 경로: ${env_file}"
            fi
        else
            log_warning "env.example 파일이 존재하지 않습니다."
        fi
    else
        log_info ".env 파일 확인됨: ${env_file}"
    fi
}
# docker-compose.yml 파일 확인
check_docker_compose_file() {
    local docker_compose_file="${PROJECT_ROOT}/docker/docker-compose.yml"
    
    if [ ! -f "${docker_compose_file}" ]; then
        log_warning "docker-compose.yml 파일이 존재하지 않습니다. 아래 경로에 파일을 생성하세요."
        log_info "docker-compose.yml 파일 경로: ${docker_compose_file}"
    else
        log_info "docker-compose.yml 파일 확인됨: ${docker_compose_file}"
    fi
}
# dockerfile 파일 확인
check_dockerfile_file() {
    local dockerfile_file="${PROJECT_ROOT}/docker/Dockerfile"

    if [ ! -f "${dockerfile_file}" ]; then
        log_warning "Dockerfile 파일이 존재하지 않습니다. 아래 경로에 파일을 생성하세요."
        log_info "Dockerfile 파일 경로: ${dockerfile_file}"
    else
        log_info "Dockerfile 파일 확인됨: ${dockerfile_file}"
    fi
}

# ------------------------------------------------------------
# 메인 로직
# ------------------------------------------------------------
case "${1:-help}" in
    build)
        # .env 파일 존재 확인
        check_env_file
        # .env 파일이 존재하면 로컬 환경에 환경변수 export (image build 시에도 필요할 수 있음)
        if [ -f "${PROJECT_ROOT}/.env" ]; then
            log_info ".env 파일에서 환경 변수 로드 중..."
            set -a
            source "${PROJECT_ROOT}/.env"
            set +a
            log_success ".env 파일에서 환경 변수 로드 완료"
        fi
        
        check_docker_compose_file
        check_dockerfile_file
        if [ -f "${PROJECT_ROOT}/docker/docker-compose.yml" ]; then
            log_info "MCP Server Image 빌드 중..."
            docker-compose -f "${PROJECT_ROOT}/docker/docker-compose.yml" build
            log_success "MCP Server Image 빌드 완료"
        fi
        ;;
    run)
        check_env_file
        if [ -f "${PROJECT_ROOT}/.env" ]; then
            log_info ".env 파일에서 환경 변수 로드 중..."
            set -a
            source "${PROJECT_ROOT}/.env"
            set +a
            log_success ".env 파일에서 환경 변수 로드 완료"
        fi

        # MCP Server Docker가 이미 실행 중인지 확인 : core service가 헬시 한 지 확인
        core_ok=0
        if is_docker_service_healthy "mcp_tavily_server" 3000; then
            core_ok=1
        fi

        # MCP Server가 실행 중이면 접속 정보 출력
        if [[ "${core_ok}" -eq 1 ]]; then
            echo ""
            log_info "MCP Server 접속 정보:"
            echo "  -Tavily MCP Server: http://localhost:3000"
        # MCP Server가 실행 중이 아니면 실행
        else
            # MCP Server가 사용할 Port를 다른 프로세스가 점유했는 지 확인
            is_port_busy=0
            for port in 3000 3001 3002; do
                if is_port_in_use "${port}" && ! is_health_ok "${port}"; then
                    is_port_busy=1
                fi
            done

            if [[ "${is_port_busy}" -eq 1 ]]; then
                log_warning "MCP Server가 사용할 Port(3000)가 다른 프로세스에 의해 점유 중인 것으로 확인됩니다."
                log_warning "해당 Port를 점유한 프로세스를 종료하거나 포트를 변경한 뒤 다시 시도하세요."
            else
                check_docker_compose_file
                if [ -f "${PROJECT_ROOT}/docker/docker-compose.yml" ]; then
                    log_info "MCP Server Background 시작 중..."
                    # -f : 사용할 compose file 지정
                    # --profile toos : 프로필 지정 (tools 프로필에 속한 서비스만 실행)
                    # up : 서비스를 생성하고 시작하는 명령어
                    # -d : 백그라운드(데몸) 모드로 실행, 터미널에서 분리되어 실행
                    docker-compose -f "${PROJECT_ROOT}/docker/docker-compose.yml" --profile tools up -d
                    
                    log_success "MCP Server가 시작되었습니다"
                    echo ""
                    log_info "MCP Server 접속 정보:"
                    echo "    - Tavily MCP Server: http://localhost:3000"
                else
                    log_error "docker-compose.yml 파일이 존재하지 않아, MCP Server를 시작할 수 없습니다."
                fi
            fi
        fi
        ;;

    stop)
        log_info "MCP Server 중지 중..."
        docker-compose -f "${PROJECT_ROOT}/docker/docker-compose.yml" down
        log_success "MCP Server가 중지되었습니다."
        ;;

    restart)
        # .env 파일 존재 시 export
        check_env_file
        if [ -f "${PROJECT_ROOT}/.env" ]; then
            log_info ".env 파일에서 환경 변수 로드 중..."
            set -a
            source "${PROJECT_ROOT}/.env"
            set +a
            log_success ".env 파일에서 환경 변수 로드 완료"
        fi

        log_info "MCP Server 재시작 중..."
        docker-compose -f "${PROJECT_ROOT}/docker/docker-compose.yml" restart
        log_success "MCP Server가 재시작되었습니다."
        ;;
    
    logs)
        if [ -n "$2" ]; then # 두번째인자 문자열이 비어있지 않으면
            case "$2" in
                tavily)
                    docker-compose -f "${PROJECT_ROOT}/docker/docker-compose.yml" logs -f tavily_server
                    ;;
            esac
        else
            docker-compose -f "${PROJECT_ROOT}/docker/docker-compose.yml" logs -f
        fi
        ;;
    
    status)
        log_info "MCP Server 상태 확인 중..."
        docker-compose -f "${PROJECT_ROOT}/docker/docker-compose.yml" ps
        ;;
    
    clean)
        log_info "미사용 컨테이너 및 이미지 정리 중..."
        docker-compose -f "${PROJECT_ROOT}/docker/docker-compose.yml" down --remove-orphans
        docker system prune -f
        log_success "정리 완료"
        ;;
    
    test)
        log_info "MCP Server 헬스체크 테스트 중..."
        echo ""

        # Tavily Server Test
        log_info "Tavily Server 테스트 (localhost:3000)..."
        if is_health_ok 3000 ; then
            log_success "Tavily Server OK"
        else
            log_error "Tavily Server 응답 없음"
        fi

        echo ""
        log_info "전체 서비스 상태:"
        docker-compose -f "${PROJECT_ROOT}/docker/docker-compose.yml" ps
        ;;

    help|--help|-h)
        show_help
        ;;
    
    *)
        log_error "알 수 없는 명령어: $1"
        echo ""
        show_help
        exit 1
        ;;
esac




        
