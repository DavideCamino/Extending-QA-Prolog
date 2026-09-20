module circ_sat (a, b, c, y);
   input a, b, c;
   output y;

   assign y = a & ~(b | c);
endmodule // circ_sat