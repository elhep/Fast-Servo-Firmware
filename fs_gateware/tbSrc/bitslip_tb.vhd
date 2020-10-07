
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

entity bitslip_tb is
--  Port ( );
end bitslip_tb;

architecture tb of bitslip_tb is
    signal tb_rst, tb_dco2d, tb_dco, tb_bitslip   :  STD_LOGIC;
    signal tb_frame_line : STD_LOGIC := '1';
    signal tb_frame : STD_LOGIC_VECTOR(3 downto 0) := "1100";
    constant period : time := 8 ns;
    constant period_dco    :   time := period/2;

begin
    UUT: entity work.bitslip port map(sys_clk =>tb_dco2d, dco_clk=>tb_dco, dco2d_clk => tb_dco2d, 
                                    dco_rst => tb_rst, dco2d_rst=> tb_rst, sys_rst=>tb_rst, 
                                    o_bitslip=>tb_bitslip, i => tb_frame_line);
    

    
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


    process (tb_dco, tb_dco2d, tb_rst)
    begin
        if tb_rst = '0' then
            if rising_edge(tb_dco) or falling_edge(tb_dco) then
                tb_frame_line <= tb_frame(3);
                tb_frame <= tb_frame(2 downto 0) & tb_frame(3);
            end if;
        end if;
    end process;
    
    

end tb;
