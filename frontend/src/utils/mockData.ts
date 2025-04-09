import { reactive, ref } from "vue"
import type { file } from "../api/file";
import type { result } from "../api/repo";

export const userId = ref('67ba8dbb7ebbf61ada209dd5');

export const curRepoId = ref('67ba8ee87ebbf61ada209dd6');

export const curFileId = ref('67babdfcfeb3983ea608df74')

export const userData = reactive({
  id: '67ba8dbb7ebbf61ada209dd5',
  username: 'dev',
  email: 'dev@example.com',
  profile_picture: null,
  repos: [
    '67ba8ee87ebbf61ada209dd6'
  ],
  collaborations: []
});

export const repoData = reactive({
  id: '67ba8ee87ebbf61ada209dd6',
  name: 'Test',
  desc: 'This is for development',
  owner_id: '67ba8dbb7ebbf61ada209dd5',
  collaborators: [],
  files: [
    {
      file_id: '67babdfcfeb3983ea608df74',
      filename: 'pic.jpeg',
      size: 251896,
      uploaded_at: '2025-02-23 06:19:40.569000',
      status: '0.4709395343113545'
    }
  ] as file[],
  results: [
    {
      source_file: false,
      file_id: '67bd33a7263f9dc0d24071b1',
      filename: 'pic.xlsx',
      size: 5942,
      uploaded_at: '2025-02-25 03:06:15.309000',
      status: 'uploaded'
    },
    {
      source_file: false,
      file_id: '67c06ea46d3f6d665b1b06fe',
      filename: 'pic.xlsx',
      size: 5887,
      uploaded_at: '2025-02-27 13:54:44.205000',
      status: 'uploaded'
    },
    {
      source_file: false,
      file_id: '67c158c1f72169f1acce8963',
      filename: '开户信息.xlsx',
      size: 9473,
      uploaded_at: '2025-02-28 06:33:37.663000',
      status: 'uploaded'
    },
    {
      source_file: false,
      file_id: '67c1599bf72169f1acce8965',
      filename: '银行账单.docx',
      size: 156487,
      uploaded_at: '2025-02-28 06:37:15.149000',
      status: 'uploaded'
    },
    {
      source_file: false,
      file_id: '67c15be8f72169f1acce8967',
      filename: 'pic.xlsx',
      size: 6045,
      uploaded_at: '2025-02-28 06:47:04.261000',
      status: 'uploaded'
    }
  ] as result[]
});

export const resultData = reactive({
  res_id: '67bd33a7263f9dc0d24071b3',
  file_id: '67babdfcfeb3983ea608df74',
  content: {
    current_transaction: [
      {
        key: '交易ID',
        value: 'TX202405100001   TX202406150002   TX202407200003'
      },
      {
        key: '交易类型',
        value: '转账'
      },
      {
        key: '交易金额',
        value: '794.97'
      },
      {
        key: '交易币种',
        value: '人民币 (RMB) - CNY    CNY'
      }
    ],
    related_transactions: [
      {
        key: '交易频率',
        value: '连续2笔类似交易'
      },
      {
        key: '小额交易',
        value: '是的'
      },
      {
        key: '设备信息',
        value: '设备类型: 网上银行'
      }
    ],
    operation_information: [
      {
        key: '交易时间',
        value: '交易时间：2025年1月9日17:34:49'
      },
      {
        key: '操作时长',
        value: '没有'
      }
    ],
    initial_account: [
      {
        key: '初始账户旧余额',
        value: '0'
      },
      {
        key: '初始账户新余额',
        value: '0'
      },
      {
        key: '初始账户开户信息',
        value: '开户时间: 2025-01-09, 开户地点: 网上银行'
      },
      {
        key: '初始账户信用等级',
        value: '没有'
      },
      {
        key: '初始账户地址',
        value: '没有'
      },
      {
        key: '初始账户年龄',
        value: '4年。'
      },
      {
        key: '初始账户职业',
        value: '根据提供的文本，初始账户职业指标是“网上银行员工”。'
      },
      {
        key: '初始账户教育水平',
        value: '无'
      },
      {
        key: '初始账户联系方式',
        value: '没有'
      }
    ],
    target_account: [
      {
        key: '目标账户旧余额',
        value: '0'
      },
      {
        key: '目标账户新余额',
        value: '0'
      },
      {
        key: '目标账户开户信息',
        value: '无'
      },
      {
        key: '目标账户信用等级',
        value: '没有'
      },
      {
        key: '目标账户地址',
        value: '对方面账户：0019****0002 对方账户名称：银联转账（云闪付）'
      },
      {
        key: '目标账户年龄',
        value: '目标账户年龄：5年（从开设到2025年1月）'
      },
      {
        key: '目标账户职业',
        value: '目标账户职业指标：没有相关信息。'
      },
      {
        key: '目标账户教育水平',
        value: '没有'
      },
      {
        key: '目标账户联系方式',
        value: '目标账户所有者已注册的联系电话或电子邮件地址是13600136000和target1@例子.com。'
      }
    ],
    fraud_detection: [
      {
        key: '是否欺诈',
        value: '没有'
      },
      {
        key: '是否标记为欺诈',
        value: '不。'
      }
    ]
  }
});
