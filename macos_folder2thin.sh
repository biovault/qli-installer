# Provide the package directory as an argument
if [ $# -ne 2 ]; then
    echo "Usage: $0 <package_directory> <arch> - where"
    echo ""
    echo "<package_directory> <arch> is the subdirectory"
    echo "containing the package to be thinned"
    echo "<arch> is the architecture required in the thin package"
    echo "this may be either arm64 or x86_64"
    exit 1
fi
find $1 -type f \
  | while read -r f; do
      info=$(lipo -info "$f" 2>/dev/null) || continue
      [[ "$info" == *"Non-fat"* ]] && continue
      echo "$f: $info"
      lipo "$f" -thin "$2" -output "$f"
    done