
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.all;
-- Uncomment the following library declaration if using
-- arithmetic functions with Signed or Unsigned values
use IEEE.NUMERIC_STD.ALL;

-- Uncomment the following library declaration if instantiating
-- any Xilinx leaf cells in this code.
library UNISIM;
use UNISIM.VComponents.all;

entity adc_tb is
--  Port ( );
end adc_tb;

architecture tb of adc_tb is
    signal tb_rst, tb_dco2d, tb_dco :  STD_LOGIC;
    signal tb_frame_line : STD_LOGIC := '1';
    signal tb_frame : STD_LOGIC_VECTOR(3 downto 0) := "1100";
    signal tb_data0 : STD_LOGIC_VECTOR(15 downto 0) := (others => '1');
    signal tb_data1 : STD_LOGIC_VECTOR(15 downto 0) := (others => '1');

    signal tb_sdo0, tb_sdo1  :   STD_LOGIC_VECTOR(3 downto 0) := "1101";
    signal tb_test_vector : STD_LOGIC_VECTOR(15 downto 0) := b"1010_1100_1110_1001";
    
    signal test_change  :   STD_LOGIC_VECTOR(1 downto 0) := "11";
    
    constant period : time := 8 ns;
    constant period_dco    :   time := period/2;

begin
    UUT: entity work.adc port map(sys_clk =>tb_dco2d, dco_clk=>tb_dco, dco2d_clk => tb_dco2d, 
                                    dco_rst => tb_rst, dco2d_rst=> tb_rst, sys_rst=>tb_rst, 
                                    o_data=>tb_data0, o_data_1 => tb_data1, i_frame => tb_frame_line, 
                                    sdos => tb_sdo0, sdos_1 => tb_sdo1);    
    clk_gen: process
    begin
        tb_dco <= '1';
        wait for period_dco/2;
        tb_dco <= '0';
        wait for period_dco/2;     
    end process;

    second_clk: process
    begin
        tb_dco2d  <= '1';
        wait for period/2;
        tb_dco2d <= '0';
        wait for period/2;
    end process;
    
    tb_rst <= '1', '0' after 12 ns;
    
    test_change <= "01" after 250 ns, "10" after 402.5 ns, "00" after 555 ns;
   
    process (tb_dco, tb_dco2d, tb_rst)
    begin
        if tb_rst = '0' then
            if rising_edge(tb_dco) or falling_edge(tb_dco) then
                tb_frame_line <= tb_frame(3);
                tb_frame <= tb_frame(2 downto 0) & tb_frame(3);
            end if;
        end if;
    end process;
    
    process
    begin
        wait until rising_edge(tb_frame_line);
            while True loop
                case (test_change) is
                -- there are four deserializers in sdo - each receives one of the test_vector's 4 bits;
                -- it means that first deser receives b'1111, second: b'0110, third: b'1010 and fourth: b'0001
                when "01" => 
                    tb_sdo0 <= tb_test_vector(15 downto 12);
                    tb_sdo1 <= "0000";
                    tb_test_vector <= tb_test_vector(11 downto 0) & tb_test_vector(15 downto 12);
                    wait for period_dco/2;
                when "10" => 
                    tb_sdo1 <= tb_test_vector(15 downto 12);
                    tb_sdo0 <= "0000";
                    tb_test_vector <= tb_test_vector(11 downto 0) & tb_test_vector(15 downto 12);
                    wait for period_dco/2;
                when "11" =>
                    tb_sdo0 <= tb_test_vector(15 downto 12);
                    tb_sdo1 <= tb_test_vector(15 downto 12);
                    tb_test_vector <= tb_test_vector(11 downto 0) & tb_test_vector(15 downto 12);
                    wait for period_dco/2;
                when others =>
                    tb_sdo0 <= "0000";
                    tb_sdo1 <= "0000";
                    wait for period_dco/2;
                end case;
            end loop;
    end process;


end tb;
