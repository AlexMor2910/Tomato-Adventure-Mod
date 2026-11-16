// @category TomatoAdventure
// Bounded candidate battle path; no ROM-byte or gameplay modifications.
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.io.*;
import java.math.BigInteger;
import java.nio.file.*;

public class TraceGimmickBattle extends GhidraScript {
	private Address a(long value) { return toAddr(value); }
	private void thumb(long start,long end) throws Exception {
		if(getInstructionAt(a(start))==null)
			currentProgram.getProgramContext().setValue(currentProgram.getRegister("TMode"),a(start),a(start),BigInteger.ONE);
		else if(!BigInteger.ONE.equals(currentProgram.getProgramContext().getValue(currentProgram.getRegister("TMode"),a(start),false)))
			throw new IllegalStateException("Mode conflict at "+a(start));
		DisassembleCommand command=new DisassembleCommand(a(start),new AddressSet(a(start),a(end)),true);
		if(!command.applyTo(currentProgram,monitor))throw new IllegalStateException(command.getStatusMsg());
	}
	public void run() throws Exception {
		String[] args=getScriptArgs();
		byte[] english=Files.readAllBytes(Paths.get(args[1]));
		long[][] windows={
			{0x080485B0L,0x0804881DL}, {0x080484CCL,0x080484F7L},
			{0x08046D60L,0x08046E3FL}, {0x0802B7F0L,0x0802BB03L},
			{0x0804B2F0L,0x0804B3E7L}, {0x0804CDECL,0x0804CE45L},
			{0x080418C0L,0x08041905L}, {0x08041C9CL,0x08041D03L},
			{0x08049890L,0x08049939L}
		};
		for(long[] w:windows)thumb(w[0],w[1]);
		for(long p=0x08048640L;p<0x08048664L;p+=4) {
			long target=Integer.toUnsignedLong(getInt(a(p)));
			if(target<0x08048664L || target>0x08048744L || (target&1)!=0)throw new IllegalStateException("Unexpected switch target");
			thumb(target,0x0804881DL);
		}
		// Earlier bounded flow may have already decoded fall-through starts.
		thumb(0x08048754L,0x0804881DL);
		try(PrintWriter out=new PrintWriter(new File(args[0]),"UTF-8")) {
			out.println("Language: "+currentProgram.getLanguageID());
			out.println("Scoped instructions; gameplay meanings require runtime verification.");
			for(long[] w:windows) {
				out.printf("BLOCK %08x..%08x%n",w[0],w[1]);
				InstructionIterator it=currentProgram.getListing().getInstructions(new AddressSet(a(w[0]),a(w[1])),true);
				while(it.hasNext()) {
					Instruction ins=it.next();out.println(ins.getAddress()+"  "+ins);
					for(var ref:ins.getReferencesFrom()) {
						out.print("  REF "+ref.getReferenceType()+" "+ref.getToAddress());
						if(ref.getReferenceType().isRead() && ins.getMnemonicString().equals("ldr"))out.printf(" literal=%08x",getInt(ref.getToAddress()));
						out.println();
					}
				}
			}
			out.println("SWITCH TARGETS (data)");
			for(long p=0x08048640L;p<0x08048664L;p+=4)out.printf("%08x = %08x%n",p,getInt(a(p)));
			out.println("RAW THUMB BL CANDIDATES TO 080485b0");
			for(long p=0x08000000L;p<0x087FFFFCL;p+=2) {
				int h=getShort(a(p))&65535,l=getShort(a(p+2))&65535;
				if((h&0xf800)!=0xf000 || (l&0xf800)!=0xf800)continue;
				int d=((h&2047)<<12)|((l&2047)<<1);if((d&0x400000)!=0)d|=~0x7fffff;
				if(p+4+d==0x080485B0L)out.printf("%08x%n",p);
			}
			out.println("ENGLISH COMPARISON (half-open bus spans)");
			for(long[] w:new long[][]{{0x080485B0L,0x08048820L},{0x08046D60L,0x08046E5CL},{0x080484CCL,0x080484FCL},{0x0802BA08L,0x0802BA50L},{0x080418C0L,0x08041910L},{0x08041C9CL,0x08041D10L},{0x08049890L,0x08049948L}}) {
				int different=0;
				for(long p=w[0];p<w[1];p++)if(getByte(a(p))!=english[(int)(p-0x08000000L)])different++;
				out.printf("%08x..%08x differing_bytes=%d%n",w[0],w[1],different);
			}
			out.println("TRACE_COMPLETE");
		}
	}
}
