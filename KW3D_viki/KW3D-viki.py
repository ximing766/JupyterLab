#导入串口与表格文件处理模块
import serial , xlwt , sys , time 
import json
import re  # 正则清洗JSON
import subprocess
import os
import motor_modbus_rtu_0308 as inst

UWB_COM = 'COM6'
UWB_BAUDRATE = 921600

ENABLE_VIKI_PARSE = True  # 开关：True 启用 viki 解析 HEX 数据，False 使用原 JSON 逻辑
VIKI_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "viki.pl")

def parse_hex_with_viki(hex_line):
    try:
        hex_line = hex_line.strip()
        payload = f"NXPUCIR => {hex_line}\n"
        si = None
        cf = 0
        if os.name == 'nt':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            cf = subprocess.CREATE_NO_WINDOW

        proc = subprocess.run(
            ['perl', VIKI_SCRIPT_PATH],
            input=payload,
            text=True,
            capture_output=True,
            startupinfo=si,
            creationflags=cf,
            timeout=2
        )
        
        output = proc.stdout
        if not output:
            return None
            
        return extract_viki_params(output)
    except Exception as e:
        return None

def extract_viki_params(output_text):
    data = {
        "Distance": 0.0, "RSSI": 0.0, "AoA_Azi": 0.0, 
        "AoA_Ele": 0.0, "Pdoa_Fst": 0.0, "Pdoa_Sec": 0.0, "nLos": 1
    }
    
    dist_cm = re.search(r"Dist:\s*(\d+)cm", output_text)
    if dist_cm: data["Distance"] = float(dist_cm.group(1))
        
    rssi_m = re.search(r"RSSI:\s*(-?\d+\.?\d*)dBm", output_text)
    if rssi_m: data["RSSI"] = float(rssi_m.group(1))
        
    azi_m = re.search(r"Azimuth:\s*(-?\d+\.?\d*)deg", output_text)
    if azi_m: data["AoA_Azi"] = float(azi_m.group(1))
        
    ele_m = re.search(r"Elevation:\s*(-?\d+\.?\d*)deg", output_text)
    if ele_m: data["AoA_Ele"] = float(ele_m.group(1))
        
    pdoa_m = re.findall(r"PDoA:\s*(-?\d+\.?\d*)", output_text)
    if len(pdoa_m) >= 1: data["Pdoa_Fst"] = float(pdoa_m[0])
    if len(pdoa_m) >= 2: data["Pdoa_Sec"] = float(pdoa_m[1])
        
    if "NLos" in output_text or "NLOS" in output_text: 
        data["nLos"] = 0
    else:
        data["nLos"] = 1
        
    return data

# 转台控制函数（完全不变）
def turntable_rotate_3D(degreeAzi):
    inst.write(degreeAzi)
    inst.query("*OPC?")

# ===================== 核心修复：数据采集与解析 =====================
def read_and_write_data(set_count, azimuth, test_count, ser, sheet, workbook):
    count = 0
    count_los = 0
    temp = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    while count < set_count:
        # 读取串口数据
        data_raw = ser.read(1024)
        if not data_raw:
            continue

        try:
            data_json = None
            
            if ENABLE_VIKI_PARSE:
                # 方案 A: 使用 Viki 解析 HEX
                hex_str = data_raw.hex().upper()
                hex_line = " ".join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
                
                if "62 00" in hex_line:
                    parts = hex_line.split("62 00")
                    for p in reversed(parts):
                        if len(p.replace(" ", "")) > 10:
                            valid_hex = "62 00" + p
                            data_json = parse_hex_with_viki(valid_hex)
                            if data_json:
                                break
                                
                if not data_json:
                    continue
                
                Distance    = data_json.get("Distance", 0.0)
                RSSI        = data_json.get("RSSI", 0.0)
                AoA_Azi     = data_json.get("AoA_Azi", 0.0)
                Pdoa_Fst    = data_json.get("Pdoa_Fst", 0.0)
                AoA_Ele     = data_json.get("AoA_Ele", 0.0)
                Pdoa_Sec    = data_json.get("Pdoa_Sec", 0.0)
                nLos        = data_json.get("nLos", 1)

            else:
                # 方案 B: 原有 JSON 解析逻辑
                line = data_raw.decode('utf-8', errors='ignore').strip()
                
                if '{"@POSITION"' in line:
                    json_start = line.find('{"@POSITION"')
                    json_end = line.rfind('}')
                    if json_start != -1 and json_end != -1:
                        json_str = line[json_start : json_end + 1]
                        json_str = json_str.replace('"CardNo": ,', '"CardNo": null,')
                        json_str = re.sub(r'"mac":\s*([0-9A-Fa-f]+)', r'"mac": "\1"', json_str)
                        data_json = json.loads(json_str)

                if not data_json:
                    continue

                Distance    = data_json.get("A1", 0.0)
                RSSI        = data_json.get("RSSI", 0.0)
                AoA_Azi     = data_json.get("AoA-Azi", 0.0)
                Pdoa_Fst    = data_json.get("Pdoa-Fst", 0.0)
                AoA_Ele     = data_json.get("AoA-Ele", 0.0)
                Pdoa_Sec    = data_json.get("Pdoa-Sec", 0.0)
                nLos        = data_json.get("nLos", 1)

            # 计数统计
            if nLos == 0:
                count_los += 1
            count += 1

            # 打印采集结果（实时看到A1正确数值）
            print(f"🎉 成功采集第{count}条 | 角度:{azimuth}°")
            print(f"📊 数据：Distance={Distance},RSSI={RSSI},AoA-Azi={AoA_Azi},Pdoa_Fst={Pdoa_Fst},AoA_Ele={AoA_Ele},Pdoa_Sec={Pdoa_Sec}")

            # 累加计算平均值
            temp[0] += Pdoa_Fst
            temp[1] += AoA_Azi
            temp[2] += Distance
            temp[3] += RSSI
            temp[4] += AoA_Ele
            temp[5] += Pdoa_Sec

            # 写入Excel（列位置完全正确）
            row = count + test_count * set_count
            sheet.write(row, 7,  count)
            sheet.write(row, 8,  azimuth)
            sheet.write(row, 9, Pdoa_Fst)
            sheet.write(row, 10, AoA_Azi)
            sheet.write(row, 11, Distance)
            # sheet.write(row, 13, nLos)
            sheet.write(row, 12, RSSI)
            sheet.write(row, 13, AoA_Ele)
            sheet.write(row, 14, Pdoa_Sec)

            # 采集够数量自动退出
            if count >= set_count:
                break

        except Exception as e:
            # 仅打印有效数据的异常，过滤无用日志
            continue

    # 计算平均值
    avg_pdoa    = temp[0] / set_count
    avg_aoa     = temp[1] / set_count
    avg_a1      = temp[2] / set_count
    avg_rssi    = temp[3] / set_count
    avg_ele     = temp[4] / set_count
    avg_pdoa2   = temp[5] / set_count
    los_rate    = f"{count_los / set_count * 100:.2f}%"
        #算本批次数据的平均值

    sheet.write(test_count+1,0,azimuth)
    #pdoa,aoa,distance平均值
    sheet.write(test_count+1,1,avg_pdoa)
    sheet.write(test_count+1,2,avg_aoa)
    sheet.write(test_count+1,3,avg_a1)
    # sheet.write(test_count+1,4,los_rate)
    sheet.write(test_count+1,4,avg_rssi)
    sheet.write(test_count+1,5,avg_ele)
    sheet.write(test_count+1,6,avg_pdoa2)

    # # 写入平均值行
    # avg_row = test_count * set_count +set_count+ 1
    # sheet.write(avg_row, 0, azimuth)
    # sheet.write(avg_row, 1, avg_pdoa)
    # sheet.write(avg_row, 2, avg_aoa)
    # sheet.write(avg_row, 3, avg_a1)
    # sheet.write(avg_row, 4, los_rate)
    # sheet.write(avg_row, 5, avg_rssi)
    # sheet.write(avg_row, 6, avg_ele)
    # sheet.write(avg_row, 7, avg_pdoa2)

    # 保存Excel
    try:
        workbook.save("研究院LHCP天线&IOS手机mini-姿态4朝右-2m_CH9.xls")
    except:
        print("💢 保存失败，请关闭Excel文件！")

# ===================== 主函数（完全不变） =====================
if __name__ == '__main__':
    # 采集参数配置
    set_count=20
    start=-60
    end=60
    step=6
    test_num=(end-start)//step
    print(f"每个角度{set_count}条，角度{start}~{end}，步长{step}，共{test_num+1}个位置")

    a = 1
    if a ==1:
        start = -start

    # Excel表头
    head=[
        "Azimuth","PDOA_Fst","AoA_Azi","Distance","RSSI","AoA_Ele","Pdoa_Sec",
        "PointCount","Azimuth","PDOA_Fst","AoA_Azi","Distance","RSSI","AoA_Ele","Pdoa_Sec"
    ]

    # 创建Excel文件
    workbook = xlwt.Workbook("utf-8")
    sheet = workbook.add_sheet("data")
    for i in range(len(head)):
        sheet.write(0,i,head[i])

    print("转台归位...")
    print("已到初始位置")

    # 打开UWB串口
    ser = serial.Serial(UWB_COM, UWB_BAUDRATE, timeout=2)
    print(f"✅ UWB串口打开成功：{UWB_COM} @ {UWB_BAUDRATE}")

    # 循环采集数据
    for i in range(test_num+1):
        turntable_rotate_3D(start)
        current_angle = -start
        print(f"\n🎯 已转到角度：{current_angle}°")

        # 等待稳定+清空缓存
        time.sleep(1)
        ser.reset_input_buffer()
        print("🔍 开始采集数据...")
        read_and_write_data(set_count, current_angle, i, ser, sheet, workbook)

        start -= step

    # 最终保存+关闭串口
    workbook.save("G5-A1-RIGHT天线&魅族手机-姿态1-0°-2.5m_CH9.xls")
    ser.close()
    print("\n🏁 测试全部完成，文件已保存！")