import pandas as pd
from label_utils import LabelUtils


class DataPreprocessor:
    def __init__(self, excel_path, chunk_size=50, debug=True):
        self.excel_path = excel_path
        self.chunk_size = chunk_size
        self.debug = debug
        self.df = pd.read_excel(excel_path)
        if self.debug:
            print(f"Excel文件已读取，共有 {len(self.df)} 行数据。")

        # 提取股票代码和提问列数据
        self.stock_codes = self.df.iloc[:, 0].tolist()  # 第一列为股票代码
        self.raw_column_df = pd.DataFrame(self.df.iloc[:, 2].values, columns=['rowtext'])  # 提取第三列数据

        if self.debug:
            print(f"提问列数据已提取，共有 {len(self.raw_column_df)} 行数据。")

        # 将股票代码和提问列数据合并
        self.raw_column_df['se_code'] = self.stock_codes
        self.processed_data = pd.DataFrame(columns=['se_code', 'rowtext', 'labeledtext'])
        self.chunk_counter = 0
        self.file_counter = 1
        self.label_utils = LabelUtils()

    def chunked_iterator(self):
        """定义一个迭代器函数，每次输出指定大小的块"""
        for start in range(0, len(self.raw_column_df), self.chunk_size):
            yield self.raw_column_df[start:start + self.chunk_size].copy()  # 创建副本

    def process_chunk(self, chunk, i):
        """处理单个块的逻辑"""
        if self.debug:
            print(f'正在处理第 {i + 1} 个块')

        raw_texts = chunk['rowtext'].tolist()
        try:
            labeled_texts = self.label_utils.label_multiple(raw_texts)
            if len(labeled_texts) != len(chunk):
                raise ValueError("标注结果长度与块行数不匹配")
            chunk.loc[:, 'labeledtext'] = labeled_texts
        except Exception as e:
            print(f"标注第 {i + 1} 个块时出错: {e}")
            return

        self.processed_data = pd.concat([self.processed_data, chunk], ignore_index=True)
        self.chunk_counter += 1

        # 每10个块或最后一个块后保存到文件
        if self.chunk_counter % 10 == 0 or len(chunk) < self.chunk_size:
            current_excel_path = f'test_{self.file_counter}.xlsx'
            self.save_to_excel(current_excel_path)
            if self.debug:
                print(f'处理 {self.chunk_counter} 个块后保存到 {current_excel_path}')
            self.file_counter += 1

    def save_to_excel(self, path):
        """保存 processed_data 到指定路径的 Excel 文件"""
        self.processed_data.to_excel(path, index=False)
        if self.debug:
            print(f"数据已保存到 {path}")

    def run_labeling(self):
        """运行数据预处理"""
        try:
            iterator = self.chunked_iterator()
            for i, chunk in enumerate(iterator):
                self.process_chunk(chunk, i)

            # 处理最后一个块
            if not self.processed_data.empty:
                final_excel_path = f'test2_{self.file_counter}.xlsx'
                self.save_to_excel(final_excel_path)
                if self.debug:
                    print(f'处理完所有块后保存到 {final_excel_path}')
        except Exception as e:
            print(f"处理数据时出错: {e}")


# 使用示例
preprocessor = DataPreprocessor('2022_test.xlsx')
preprocessor.run_labeling()