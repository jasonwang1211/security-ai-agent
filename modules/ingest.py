# src/ingestor.py
import re

class LogIngestor:
    def __init__(self, file_path):
        self.file_path = file_path
        # 使用 Regex 解析 Common Log Format
        self.log_pattern = re.compile(
            r'(?P<ip>\d+\.\d+\.\d+\.\d+) - - \[(?P<timestamp>.*?)\] "(?P<method>\w+) (?P<path>.*?) HTTP/.*?" (?P<status>\d+) (?P<size>\d+)'
        )

    def parse_logs(self):
        parsed_data = []
        try:
            with open(self.file_path, 'r') as file:
                for line in file:
                    match = self.log_pattern.match(line)
                    if match:
                        parsed_data.append(match.groupdict())
            return parsed_data
        except FileNotFoundError:
            print(f"Error: File {self.file_path} not found.")
            return []
