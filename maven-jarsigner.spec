Name:		maven-jarsigner
Version:	3.1.0
Release:	1
Summary:	Maven component that signs and verifies JAR files
Group:		Development/Java
License:	Apache-2.0
URL:		https://maven.apache.org/shared/maven-jarsigner/
Source0:	https://github.com/apache/maven-jarsigner/archive/refs/tags/maven-jarsigner-%{version}.tar.gz#/maven-jarsigner-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	python
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildRequires:	mvn(org.apache.maven.shared:maven-shared-utils)
BuildRequires:	maven-shared-utils >= 3.5.0
Requires:	maven-shared-utils >= 3.5.0
BuildRequires:	mvn(commons-io:commons-io)
BuildRequires:	apache-commons-io >= 1:2.22.0
Requires:	apache-commons-io >= 1:2.22.0
BuildRequires:	mvn(org.slf4j:slf4j-api)
BuildRequires:	mvn(javax.inject:javax.inject)
# javax.inject and jakarta-inject both provide this coordinate.
BuildRequires:	javax.inject >= 1-2
Requires:	javax.inject >= 1-2
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
Builds the jarsigner command line and runs it to sign or verify a
JAR. 3.1.0 uses maven-shared-utils 3.5 and commons-io. Tests need
JUnit Jupiter and Guice 6, so they are not run.

%prep
%autosetup -n maven-jarsigner-maven-jarsigner-%{version}
rm -rf src/test .github
python - <<'PY'
import xml.etree.ElementTree as ET
NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)

def tag(name):
    return "{" + NS + "}" + name

def add(parent, name, text):
    node = ET.SubElement(parent, tag(name))
    node.text = text
    return node

root = ET.Element(tag("project"))
add(root, "modelVersion", "4.0.0")
add(root, "groupId", "org.apache.maven.shared")
add(root, "artifactId", "maven-jarsigner")
add(root, "version", "%{version}")
add(root, "name", "Apache Maven Jarsigner")
props = ET.SubElement(root, tag("properties"))
add(props, "maven.compiler.release", "8")
add(props, "project.build.sourceEncoding", "UTF-8")
deps = ET.SubElement(root, tag("dependencies"))
for group, artifact, version in (
    ("org.apache.maven.shared", "maven-shared-utils", "3.5.0"),
    ("commons-io", "commons-io", "2.22.0"),
    ("org.slf4j", "slf4j-api", "1.7.36"),
    ("javax.inject", "javax.inject", "1"),
):
    dep = ET.SubElement(deps, tag("dependency"))
    add(dep, "groupId", group)
    add(dep, "artifactId", artifact)
    add(dep, "version", version)
ET.ElementTree(root).write("pom.xml", encoding="utf-8", xml_declaration=True)
PY
# Sisu loads @Named classes from this index. The indexer plugin is not packaged.
python - <<'PY'
import re
from pathlib import Path
root = Path("src/main/java")
names = []
for path in sorted(root.rglob("*.java")):
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*?$", "", text, flags=re.M)
    match = re.search(r"\b(?:class|interface|enum)\s+([A-Za-z0-9_]+)", text)
    if not match:
        continue
    if "@Named" not in text[:match.start()]:
        continue
    pkg = re.search(r"(?m)^package\s+([A-Za-z0-9_.]+)\s*;", text)
    if not pkg:
        continue
    names.append(pkg.group(1) + "." + match.group(1))
if names:
    dest = Path("src/main/resources/META-INF/sisu")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "javax.inject.Named").write_text("\n".join(names) + "\n", encoding="utf-8")
PY

%files -f .mfiles
%doc README.md README.TXT
