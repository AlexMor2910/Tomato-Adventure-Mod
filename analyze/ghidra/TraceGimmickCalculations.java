// @category TomatoAdventure
// Read-only ROM analysis; only disposable database metadata is changed.
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.Reference;
import java.io.*;
import java.math.BigInteger;
import java.nio.file.*;
import java.util.*;

public class TraceGimmickCalculations extends GhidraScript {
	private Address a(long v) { return toAddr(v); }
	private void thumb(long start, long end) throws Exception {
		if (getInstructionAt(a(start)) == null)
			currentProgram.getProgramContext().setValue(currentProgram.getRegister("TMode"), a(start), a(start), BigInteger.ONE);
		else if (!BigInteger.ONE.equals(currentProgram.getProgramContext().getValue(currentProgram.getRegister("TMode"), a(start), false)))
			throw new IllegalStateException("Mode conflict at " + a(start));
		DisassembleCommand cmd = new DisassembleCommand(a(start), new AddressSet(a(start),a(end)), true);
		if (!cmd.applyTo(currentProgram, monitor)) throw new IllegalStateException("Disassembly failed: " + cmd.getStatusMsg());
	}
	private void dump(PrintWriter out, long start, long end) throws Exception {
		out.printf("BLOCK %08x..%08x (inclusive window, data gaps omitted)%n",start,end);
		var it=currentProgram.getListing().getInstructions(new AddressSet(a(start),a(end)),true);
		while(it.hasNext()) {
			Instruction ins=it.next();
			out.println(ins.getAddress()+"  "+ins);
			for(Reference ref:ins.getReferencesFrom()) {
				out.print("  REF "+ref.getReferenceType()+" "+ref.getToAddress());
				if(ref.getReferenceType().isRead() && ins.getMnemonicString().equals("ldr")) {
					try { out.printf(" literal=%08x",getInt(ref.getToAddress())); } catch(Exception ignored) { }
				}
				out.println();
			}
		}
	}
	private int half(byte[] bytes,int p) { return (bytes[p]&255)|((bytes[p+1]&255)<<8); }
	private long word(byte[] bytes,int p) { return Integer.toUnsignedLong(half(bytes,p)|(half(bytes,p+2)<<16)); }
	public void run() throws Exception {
		String[] args=getScriptArgs();
		byte[] rom=new byte[0x800000];
		if(currentProgram.getMemory().getBytes(a(0x08000000L),rom)!=rom.length) throw new IllegalStateException("ROM mapping/length mismatch");
		byte[] english=Files.readAllBytes(Paths.get(args[1]));
		currentProgram.getMemory().createUninitializedBlock("IWRAM",a(0x03000000L),0x8000,false);
		long[][] calc={{0x08075970L,0x080759CFL},{0x08075AB0L,0x08075AB1L},{0x08075AB2L,0x08075AEDL}};
		for(long[] w:calc) thumb(w[0],w[1]);
		for(int i=0;i<9;i++) { long p=0x08075A04L+i*0x14; thumb(p,p+0x0d); }
		long[][] windows={
			{0x0807565CL,0x080756A7L},{0x080754B0L,0x080754D3L},
			{0x08069F60L,0x08069F87L},{0x080F7B08L,0x080F7B9DL},
			{0x08076E28L,0x08077067L},{0x080770A8L,0x08077267L},
			{0x08078550L,0x0807864DL},{0x0807892CL,0x08078BDBL},
			{0x08078CACL,0x08078DA7L},{0x0807995CL,0x08079A51L},
			{0x08080C84L,0x08080CD1L},{0x08080D4CL,0x08080DAFL},
			{0x08080E28L,0x08080E4DL},{0x08080E54L,0x08080E75L},
			{0x08080E84L,0x08080ED9L},{0x08080EF8L,0x08080F67L},
			{0x080742B8L,0x08074307L},{0x080744FCL,0x080745B7L},
			{0x08081340L,0x080813FFL},{0x08079B78L,0x08079BF9L},
			{0x08079AE4L,0x08079B61L},{0x080791E8L,0x08079331L},
			{0x08079C14L,0x08079C7FL},{0x08081188L,0x080811C9L},
			{0x08076C3CL,0x08076CCBL},{0x08076CE0L,0x08076E23L}
		};
		for(long[] w:windows) thumb(w[0],w[1]);
		// Computed item dispatch: explicit switch tables, not guessed flow.
		for(long table:new long[]{0x08080CD8L,0x08080DB4L}) {
			for(int i=0;i<29;i++) {
				long target=word(rom,(int)(table-0x08000000L)+i*4);
				if(target<0x08080D4CL || target>0x08080F0CL || (target&1)!=0) throw new IllegalStateException("Unexpected dispatch target "+a(target));
				// Decode only actual targets from the evidenced dispatch tables.
				if(getInstructionAt(a(target))==null) {
					boolean bounded=false;
					for(long[] w:windows) if(target>=w[0] && target<=w[1]) {thumb(target,w[1]);bounded=true;break;}
					if(!bounded) throw new IllegalStateException("Missing bounded dispatch seed at "+a(target));
				}
			}
		}
		AddressSet body=new AddressSet();
		for(long[] w:calc) body.add(a(w[0]),a(w[1]));
		for(int i=0;i<9;i++) {long p=0x08075A04L+i*0x14; body.add(a(p),a(p+0x0d));}
		currentProgram.getFunctionManager().createFunction(null,a(0x08075970L),body,ghidra.program.model.symbol.SourceType.ANALYSIS);
		int count=0;
		for(AddressRange span:body) {
			long p=span.getMinAddress().getOffset(),end=span.getMaxAddress().getOffset()+1;
			while(p<end) {Instruction ins=getInstructionAt(a(p)); if(ins==null || p+ins.getLength()>end) throw new IllegalStateException("Calculation coverage gap "+a(p)); p+=ins.getLength();count++;}
		}
		try(PrintWriter out=new PrintWriter(new File(args[0]),"UTF-8")) {
			out.println("Language: "+currentProgram.getLanguageID());
			out.println("Calculation instruction count: "+count);
			out.println("Parameters and gameplay meanings must be inferred from instructions, not assigned by this script.");
			out.println("COMPLETE CALCULATION FUNCTION");
			dump(out,0x08075970L,0x08075AEDL);
			out.println("CALLER SCANS (raw candidates, context validation follows)");
			for(int p=0;p<rom.length-3;p+=2) {
				int h=half(rom,p),l=half(rom,p+2);
				if((h&0xf800)==0xf000 && (l&0xf800)==0xf800) {
					int d=((h&2047)<<12)|((l&2047)<<1); if((d&0x400000)!=0)d|=~0x7fffff;
					if(0x08000000L+p+4+d==0x08075970L)out.printf("THUMB BL %08x%n",p+0x08000000L);
				}
			}
			int pointerMatches=0;
			for(int p=0;p<rom.length-3;p++) {
				long v=word(rom,p); if(v==0x08075970L || v==0x08075971L) {out.printf("RAW POINTER %08x = %08x%n",p+0x08000000L,v);pointerMatches++;}
			}
			out.println("Raw pointer matches (all alignments): "+pointerMatches);
			out.println("CACHE OFFSET RAW WORD MATCHES (aligned literal candidates, not complete alias xrefs)");
			for(int p=0;p<rom.length-3;p+=4) {
				long v=word(rom,p);
				if(v==0x5ae8L || v==0x5af0L || v==0x5af2L || v==0x5af4L)out.printf("%08x = %08x%n",p+0x08000000L,v);
			}
			out.println("CALLER AND CALLEE CONTEXTS");
			for(long[] w:windows) dump(out,w[0],w[1]);
			out.println("SWITCH DATA");
			for(long[] span:new long[][]{{0x080759E0L,0x08075A04L},{0x08080CD8L,0x08080D4CL},{0x08080DB4L,0x08080E28L}})
				for(long p=span[0];p<span[1];p+=4)out.printf("%08x = %08x%n",p,getInt(a(p)));
			out.println("ENGLISH COMPARISON (half-open file-derived windows, no English ROM writes)");
			for(long[] w:new long[][]{{0x08075970L,0x08075AFCL},{0x0807565CL,0x080756A8L},{0x08079AE4L,0x08079B78L},{0x08081188L,0x080811D0L}}) {
				int diffs=0;
				for(int p=(int)(w[0]-0x08000000L);p<(int)(w[1]-0x08000000L);p++)if(rom[p]!=english[p])diffs++;
				out.printf("%08x..%08x differing_bytes=%d%n",w[0],w[1],diffs);
			}
			out.println("TRACE_COMPLETE");
		}
	}
}
