import adc
import si5340
import dac

def main():
    si5340.configure_si5340()
    adc.main()
    dac.main()

if __name__ == "__main__":
    main()