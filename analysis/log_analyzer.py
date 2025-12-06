import os
import json
from collections import Counter
import glob

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))

def analyze_logs():
    """지정된 디렉토리의 모든 로그 파일을 분석합니다."""
    log_files = glob.glob(os.path.join(LOG_DIR, "app.log*"))
    if not log_files:
        print(f"분석할 로그 파일이 '{LOG_DIR}'에 없습니다.")
        return

    print(f"총 {len(log_files)}개의 로그 파일을 분석합니다: {log_files}")

    total_requests = 0
    status_codes = Counter()
    endpoints = Counter()
    total_process_time = 0.0
    error_count = 0
    error_messages = Counter()

    for file_path in log_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        
                        # 요청 로그만 필터링 (request_id가 있는 경우)
                        if "request_id" in log_entry:
                            total_requests += 1
                            
                            if "status_code" in log_entry:
                                status_codes[log_entry["status_code"]] += 1
                            
                            if "url" in log_entry:
                                endpoints[log_entry["url"]] += 1
                            
                            if "process_time_seconds" in log_entry:
                                total_process_time += float(log_entry["process_time_seconds"])
                            
                            # 에러 레벨 로그 처리
                            if log_entry.get("levelname") == "ERROR":
                                error_count += 1
                                if "error_message" in log_entry:
                                    error_messages[log_entry["error_message"]] += 1

                    except json.JSONDecodeError:
                        # JSON 파싱이 불가능한 라인은 건너뜠니다.
                        continue
        except Exception as e:
            print(f"'{file_path}' 파일 처리 중 오류 발생: {e}")

    print_report(total_requests, status_codes, endpoints, total_process_time, error_count, error_messages)

def print_report(total_requests, status_codes, endpoints, total_process_time, error_count, error_messages):
    """분석 결과를 출력합니다."""
    print("\n--- 로그 분석 ---")
    
    if total_requests == 0:
        print("분석할 요청 데이터가 없습니다.")
        return

    avg_process_time = (total_process_time / total_requests) if total_requests > 0 else 0

    print(f"총 요청 수: {total_requests}")
    print(f"총 에러 수: {error_count}")
    print(f"평균 처리 시간: {avg_process_time:.4f} 초")

    print("\n[상태 코드별 요청 수]")
    for code, count in sorted(status_codes.items()):
        print(f"- {code}: {count} 회")

    print("\n[요청이 많은 엔드포인트 Top 5]")
    for endpoint, count in endpoints.most_common(5):
        print(f"- {endpoint}: {count} 회")
        
    if error_count > 0:
        print("\n[주요 에러 메시지 Top 5]")
        for msg, count in error_messages.most_common(5):
            print(f"- {msg}: {count} 회")


if __name__ == "__main__":
    analyze_logs()
