// Standard Java compiler adapter: read dependency classes with JarFile instead
// of JDK ZipFS/toRealPath, which fails in this Windows environment.
import java.io.*;
import java.net.URI;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;
import javax.tools.*;

public class CompileScript {
	private static class JarClass extends SimpleJavaFileObject {
		final JarFile jar;
		final String entry, binaryName;
		JarClass(JarFile jar, String entry) {
			super(URI.create("mem:///" + entry), Kind.CLASS);
			this.jar=jar; this.entry=entry;
			binaryName=entry.substring(0,entry.length()-6).replace('/','.');
		}
		@Override public InputStream openInputStream() throws IOException {
			return jar.getInputStream(jar.getJarEntry(entry));
		}
	}
	public static void main(String[] args) throws Exception {
		Path install=Paths.get(args[0]), source=Paths.get(args[1]), output=Paths.get(args[2]);
		List<JarFile> jars=new ArrayList<>();
		Map<String,JarClass> classes=new LinkedHashMap<>();
		List<Path> paths=new ArrayList<>();
		try (var stream=Files.walk(install.resolve("Ghidra/Framework"))) {
			stream.filter(p->p.toString().endsWith(".jar")).sorted().forEach(paths::add);
		}
		paths.add(install.resolve("Ghidra/Features/Base/lib/Base.jar"));
		try {
			for (Path path:paths) {
				JarFile jar=new JarFile(path.toFile()); jars.add(jar);
				var entries=jar.entries();
				while (entries.hasMoreElements()) {
					String entry=entries.nextElement().getName();
					if (entry.endsWith(".class") && !entry.startsWith("META-INF/")) {
						JarClass cls=new JarClass(jar,entry); classes.putIfAbsent(cls.binaryName,cls);
					}
				}
			}
			JavaCompiler compiler=ToolProvider.getSystemJavaCompiler();
			if (compiler==null) throw new IllegalStateException("A JDK is required.");
			try (StandardJavaFileManager standard=compiler.getStandardFileManager(null,null,null)) {
				standard.setLocationFromPaths(StandardLocation.CLASS_PATH,List.of());
				JavaFileManager manager=new ForwardingJavaFileManager<StandardJavaFileManager>(standard) {
					@Override public Iterable<JavaFileObject> list(Location loc,String pkg,Set<JavaFileObject.Kind> kinds,boolean recurse) throws IOException {
						if (loc!=StandardLocation.CLASS_PATH) return super.list(loc,pkg,kinds,recurse);
						List<JavaFileObject> result=new ArrayList<>();
						if (!kinds.contains(JavaFileObject.Kind.CLASS)) return result;
						String prefix=pkg.isEmpty()?"":pkg+".";
						for (JarClass cls:classes.values()) {
							String name=cls.binaryName;
							if (name.startsWith(prefix) && (recurse || name.indexOf('.',prefix.length())<0)) result.add(cls);
						}
						return result;
					}
					@Override public String inferBinaryName(Location loc,JavaFileObject file) {
						return file instanceof JarClass cls?cls.binaryName:super.inferBinaryName(loc,file);
					}
					@Override public JavaFileObject getJavaFileForInput(Location loc,String name,JavaFileObject.Kind kind) throws IOException {
						if (loc==StandardLocation.CLASS_PATH && kind==JavaFileObject.Kind.CLASS) return classes.get(name);
						return super.getJavaFileForInput(loc,name,kind);
					}
				};
				boolean ok=compiler.getTask(null,manager,null,List.of("-proc:none","-d",output.toString()),null,
					standard.getJavaFileObjects(source.toFile())).call();
				if (!ok) throw new IllegalStateException("Script compilation failed.");
			}
		} finally { for (JarFile jar:jars) jar.close(); }
		System.out.println("Compiled script using standard JavaFileManager adapter.");
	}
}
