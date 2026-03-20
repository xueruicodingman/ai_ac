import { ArrowLeft, Download, Edit2, Save, FileText } from 'lucide-react';
import { useState } from 'react';

interface JudgeManualProps {
  onBack: () => void;
}

export default function JudgeManual({ onBack }: JudgeManualProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isGenerated, setIsGenerated] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [manualContent, setManualContent] = useState('');

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      const content = `# 评委手册

## 一、测评说明

本次评估采用多维度综合测评方式，包含以下几个环节：

### 1. BEI行为事件访谈（60分钟）
- 目的：了解被测者过去的真实行为表现
- 评估能力：领导力、沟通协作
- 评分要点：关注具体事例的STAR结构

### 2. 无领导小组讨论（90分钟）
- 目的：观察被测者在团队协作中的表现
- 评估能力：沟通协作、领导力、创新能力
- 评分要点：观察发言质量、倾听能力、影响力

### 3. 角色扮演（45分钟）
- 目的：评估被测者在特定情境下的应对能力
- 评估能力：沟通协作、问题解决
- 评分要点：关注应变能力、同理心

### 4. 案例分析（120分钟）
- 目的：考察被测者的逻辑思维和决策能力
- 评估能力：分析思维、创新能力
- 评分要点：方案可行性、分析深度

### 5. 个人愿景（30分钟）
- 目的：了解被测者的职业发展规划
- 评估能力：事业心、学习能力
- 评分要点：目标清晰度、行动计划

## 二、评分标准

### 领导力
- 5分：能够清晰设定目标，有效激励团队，展现强大的影响力
- 4分：能够设定目标并推动执行，具备一定影响力
- 3分：能够执行既定目标，偶尔展现领导行为
- 2分：较少展现领导行为，主要听从他人指挥
- 1分：完全没有展现领导力

### 沟通协作
- 5分：表达清晰有力，善于倾听，能够促进团队共识
- 4分：表达清晰，愿意倾听，能够配合团队
- 3分：基本能够表达观点，偶尔倾听他人
- 2分：表达不够清晰，较少倾听他人
- 1分：无法有效沟通

## 三、注意事项

1. **客观记录**：详细记录被测者的具体行为表现，避免主观判断
2. **独立评分**：评委之间不要相互讨论分数
3. **行为证据**：评分需要基于观察到的具体行为
4. **时间控制**：严格控制各环节时间，确保测评顺利进行

## 四、行为记录表

| 时间 | 被测者 | 行为描述 | 相关能力 | 评分 |
|-----|-------|---------|---------|-----|
| 09:30 | 张三 | 主动提出解决方案并说服团队采纳 | 领导力 | 5 |
| 09:35 | 李四 | 认真倾听他人观点并总结要点 | 沟通协作 | 4 |
| ... | ... | ... | ... | ... |
`;
      setManualContent(content);
      setIsGenerated(true);
      setIsGenerating(false);
    }, 2000);
  };

  const handleSave = () => {
    setIsEditing(false);
    alert('评委手册已保存！');
  };

  const handleSubmit = () => {
    alert('评委手册已提交定稿！');
  };

  const handleDownload = (format: 'word' | 'pdf') => {
    alert(`正在下载${format === 'word' ? 'Word' : 'PDF'}格式评委手册...`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft size={20} />
              <span>返回</span>
            </button>
            <div className="h-6 w-px bg-gray-300" />
            <h1 className="font-semibold text-gray-900">评委手册</h1>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <FileText className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <h3 className="font-medium text-green-900 mb-1">评委手册</h3>
              <p className="text-sm text-green-700">
                根据您已提交的题本自动生成，包含测评说明、评分标准、注意事项等内容。
              </p>
            </div>
          </div>
        </div>

        {!isGenerated && (
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed mb-6"
          >
            {isGenerating ? '正在生成中...' : '生成评委手册'}
          </button>
        )}

        {isGenerated && (
          <>
            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-gray-900">评委手册内容</h3>
                <span className="text-sm text-gray-500">可编辑</span>
              </div>

              {isEditing ? (
                <textarea
                  value={manualContent}
                  onChange={(e) => setManualContent(e.target.value)}
                  className="w-full h-[500px] p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono text-sm"
                />
              ) : (
                <div className="bg-gray-50 rounded-lg p-6 max-h-[500px] overflow-y-auto">
                  <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">{manualContent}</pre>
                </div>
              )}
            </div>

            <div className="flex gap-4 mb-6">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
              >
                {isEditing ? (
                  <>
                    <Save size={18} />
                    完成编辑
                  </>
                ) : (
                  <>
                    <Edit2 size={18} />
                    编辑
                  </>
                )}
              </button>
              <button
                onClick={() => handleDownload('word')}
                className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
              >
                <Download size={18} />
                Word
              </button>
              <button
                onClick={() => handleDownload('pdf')}
                className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
              >
                <Download size={18} />
                PDF
              </button>
            </div>

            <button
              onClick={handleSubmit}
              className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              提交定稿
            </button>
          </>
        )}
      </main>
    </div>
  );
}
