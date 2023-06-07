import csv

power_nets = ["GND", "P3V3", "VIN", "VCCIO35", "1.8V", "VBAT_IN", "SHIELD", "SIN_N", "SIN_P", "SOUT_N", "S_OUT_P",
            "VCCIO34", "VCCIO33", "VCCIO13", "1.5V", "3.3V"]

c_data = {"jb1" : {}, "jb2": {}, "jb3": {}}

module_data = {"jb1": {}, "jb2": {}, "jb3": {}}
assigned = {}



for c_name in module_data.keys():
    conn_header = {}
    with open(f"{c_name}.csv", newline="\n") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            if row["Display Name"] not in power_nets:
                # conn_header.update(row["Pin Designator"]: {})
                if row["Net Name"] != "":
                    conn_header.update({row["Pin Designator"] : (row["Net Name"], row["Display Name"])})
                # print(row["Pin Designator"], row["Net Name"], row["Display Name"])
    module_data[c_name] = conn_header



with open("fast_servo_pinout.csv", newline='\n') as f:
    reader = csv.DictReader(f, delimiter=';')
    for ix, row in enumerate(reader):
        if int(row["Index"]) > 260:
            break
        c_data[row["C-Name"].lower()].update(
            {row["C-Pin"] : (row["Module Net Name"], row["FPGA Pin Name"])}
        )


for (mod_key, mod), (fs_key, fs) in zip(module_data.items(), c_data.items()):
    for pin_no, (signal_name, carrier_pin_name) in mod.items():
        # print(pin_no, signal_name, carrier_pin_name)
        assigned.update({signal_name: fs[pin_no][1]})
        # print(fs[pin_no])

with open("assigned.txt", "w") as f:
    for signal, fpga_pin in assigned.items():
        f.write(f"{signal}\t{fpga_pin}\r\n")
