using Newtonsoft.Json; // 需要安装 Newtonsoft.Json NuGet 包
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls; // 处理 TextBox, StackPanel 等控件
using System.Windows.Media;   // 处理 Brushes (颜色)
using System.Windows.Input;   // 处理 Cursors (光标)

namespace MaterialCalculator
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        // 点击按钮触发

        // 1. 点击“+添加物品”按钮时触发
        private void AddInventoryRow_Click(object sender, RoutedEventArgs e)
        {
            AddInventoryRow();
        }

        // 2. 核心添加函数
        private void AddInventoryRow(string name = "", string qty = "0")
        {
            StackPanel row = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 2, 0, 2) };

            TextBox nameInput = new TextBox { Width = 150, Text = name, Margin = new Thickness(0, 0, 5, 0), VerticalContentAlignment = VerticalAlignment.Center };
            TextBox qtyInput = new TextBox { Width = 60, Text = qty, Margin = new Thickness(0, 0, 5, 0), VerticalContentAlignment = VerticalAlignment.Center };

            Button delBtn = new Button
            {
                Content = " ✖ ",
                Foreground = Brushes.Red,
                Background = Brushes.Transparent,
                BorderThickness = new Thickness(0),
                Cursor = Cursors.Hand
            };

            delBtn.Click += (s, e) => InventoryContainer.Children.Remove(row);

            row.Children.Add(nameInput);
            row.Children.Add(qtyInput);
            row.Children.Add(delBtn);
            InventoryContainer.Children.Add(row);
        }

        private async void CalculateButton_Click(object sender, RoutedEventArgs e)
        {
            string item = TargetItemInput.Text;
            string qty = TargetQtyInput.Text;

            // 构造库存 JSON (模拟数据，实际应从 InventoryItemsControl 获取)
            var inv = new Dictionary<string, double>();

            foreach (StackPanel row in InventoryContainer.Children)
            {
                // row.Children[0] 是名称框，row.Children[1] 是数量框
                var nameBox = row.Children[0] as TextBox;
                var qtyBox = row.Children[1] as TextBox;

                if (nameBox != null && !string.IsNullOrWhiteSpace(nameBox.Text))
                {
                    double.TryParse(qtyBox.Text, out double val);
                    inv[nameBox.Text] = val;
                }
            }
            string invJson = JsonConvert.SerializeObject(inv);

            // 显示加载状态
            CalculateButton.IsEnabled = false;
            TreeOutput.Text = "计算中，请稍候...";

            try
            {
                string resultJson = await Task.Run(() => CallPythonBridge(item, qty, invJson));
                var data = JsonConvert.DeserializeObject<dynamic>(resultJson);

                if (data.error != null)
                {
                    MessageBox.Show("错误: " + data.error);
                }
                else
                {
                    // 更新 UI
                    UpdateUI(data);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("执行失败: " + ex.Message);
            }
            finally
            {
                CalculateButton.IsEnabled = true;
            }
        }

        private string CallPythonBridge(string item, string qty, string invJson)
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;

                // 现在直接定位打包好的 bridge.exe
                string bridgeExe = Path.Combine(baseDir, "bridge.exe");

                if (!File.Exists(bridgeExe))
                {
                    return "{\"success\": false, \"error\": \"未找到核心计算组件 bridge.exe\"}";
                }

                ProcessStartInfo start = new ProcessStartInfo();
                start.FileName = bridgeExe; // 直接运行 exe

                // 参数不再需要脚本路径，直接传数据
                start.Arguments = $"\"{item}\" {qty} \"{invJson.Replace("\"", "\\\"")}\"";

                start.UseShellExecute = false;
                start.RedirectStandardOutput = true;
                start.RedirectStandardError = true;
                start.CreateNoWindow = true;
                start.StandardOutputEncoding = Encoding.UTF8;

                using (Process process = Process.Start(start))
                {
                    using (StreamReader reader = process.StandardOutput)
                    {
                        return reader.ReadToEnd();
                    }
                }
            }
            catch (Exception ex)
            {
                return "{\"success\": false, \"error\": \"启动计算组件失败: " + ex.Message + "\"}";
            }
        }

        private void UpdateUI(dynamic data)
        {
            // 1. 填充左侧：合成树
            TreeOutput.Text = data.tree_view;

            // 2. 填充右上：基础材料总缺口
            BaseMaterialOutput.Text = data.base_materials;

            // 3. 填充右下：层级生产清单
            StringBuilder sb = new StringBuilder();
            sb.AppendLine($"[L0] 最终目标缺口: {TargetItemInput.Text} x {TargetQtyInput.Text}");

            // 注意：dynamic 类型在遍历嵌套字典时需要特殊处理
            foreach (var level in data.level_stats)
            {
                sb.AppendLine($"\n--- 第 {level.Name} 层 (L{level.Name}) 生产任务 ---");
                foreach (var item in level.Value)
                {
                    sb.AppendLine($"  {item.Name}: {item.Value:F2}"); // 保留两位小数
                }
            }
            LevelTaskOutput.Text = sb.ToString();
        }
    }
}