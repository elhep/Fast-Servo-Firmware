import mmap
import os
import time

from common import (
    LED0_BASE_ADDR,
    LED1_BASE_ADDR,
    LED2_BASE_ADDR,
    LED3_BASE_ADDR,
    MAP_MASK,
    PAGESIZE,
)

ON = 1
OFF = 0


def main():
    addrs = [LED0_BASE_ADDR, LED1_BASE_ADDR, LED2_BASE_ADDR, LED3_BASE_ADDR]

    f = os.open("/dev/mem", os.O_SYNC | os.O_RDWR)
    for addr in addrs:
        with mmap.mmap(
            f,
            PAGESIZE,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=addr & ~MAP_MASK,
        ) as mem:
            for i in range(6):
                start_addr = addr & MAP_MASK
                stop_addr = start_addr + 4
                print(
                    f"addr: 0x{addr:x}\tstart_addr: 0x{start_addr}\tstop_addr: 0x{stop_addr}"
                )
                mem[start_addr:stop_addr] = ON.to_bytes(4, "little")
                contents = mem[start_addr:stop_addr]
                time.sleep(0.5)
                mem[start_addr:stop_addr] = OFF.to_bytes(4, "little")
                contents = mem[start_addr:stop_addr]
                time.sleep(0.5)

    os.close(f)


if __name__ == "__main__":
    main()
