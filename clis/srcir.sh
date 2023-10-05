# ==================================================
# AUTHOR: coshz@github
# DATE: 2023.10.2
# --------------------------------------------------

SHELL_PROG="srcir"
SHELL_VER="0.1.0"
SHELL_DESC="A mangager for source packages"

Help()
{
   echo $SHELL_DESC
   echo "commands"
   echo "  help              Print this help"
   echo "  list              List all packages"
   echo "  view              Preview new package to link"
   echo "  link   <pkg>      Create links of a package"
   echo "  unlink <pkg>      Remove links of a package"
   echo "  info   <pkg>      The information of a package"
   echo "  -h, --help        Same as help"
   echo "  -v, --version     Version information"
}

View()
{
   local pkg ver bin inc lib cmk pc
   pkg=$1
   ver=$2
   if [ -z $ver ]; then
      ver=$(basename `find "$source/$pkg" -d 1 -type d`)
   fi

   bin="find $source/$pkg/$ver/bin -d 1 -not -path '*/.*' -execdir printf \"bin/%s\\n\" {} \\; 2>/dev/null"
   inc="find $source/$pkg/$ver/include -d 1 -not -path '*/.*' -execdir printf \"include/%s\\n\" {} \\; 2>/dev/null"
   lib="find $source/$pkg/$ver/lib -d 1 -type f -not -path '*/.*' -execdir printf \"lib/%s\\n\" {} \\; 2>/dev/null"
   cmk="find $source/$pkg/$ver/lib/cmake -d 1 -not -path '*/.*' -execdir printf \"lib/cmake/%s\\n\" {} \\; 2>/dev/null"
   pc="find $source/$pkg/$ver/lib/pkgconfig -d 1 -not -path '*/.*' -execdir printf \"lib/pkgconfig/%s\\n\" {} \\; 2>/dev/null"

   jq -n \
      --arg jpkg "$pkg" \
      --arg jver "$ver" \
      --arg jsrc "$source/$pkg/$ver" \
      --arg jtgt "$target" \
      --argjson jbin "$(eval $bin | jq -R . | jq -s .)" \
      --argjson jinc "$(eval $inc | jq -R . | jq -s .)" \
      --argjson jlib "$(eval $lib | jq -R . | jq -s .)" \
      --argjson jcmk "$(eval $cmk | jq -R . | jq -s .)" \
      --argjson jpc "$(eval $pc | jq -R . | jq -s .)" \
      '{
         $jpkg:{
            ver:$jver,
            src:$jsrc,
            tgt:$jtgt,
            bin:$jbin,
            include:$jinc,
            lib:$jlib,
            cmake:$jcmk,
            pkgconfig:$jpc
         }
      }'
}

List()
{
   jq 'keys' $config
}

Info()
{
   local pkg=$1
   jq ".$pkg" $config
}

Link()
{
   local pkg jpkg src_prefix tgt_prefix
   pkg=$1
   jpkg=$(View $pkg)
   src_prefix=$(jq -r --arg pkg $pkg '.[$pkg] .src' <<< $jpkg)
   tgt_prefix=$(jq -r --arg pkg $pkg '.[$pkg] .tgt' <<< $jpkg)

   for it in "include" "lib" "cmake" "pkgconfig"; do
      links="jq -r '.$pkg .$it []' <<< \$jpkg"
      for f in $(eval $links); do
         ln -sf "$src_prefix/$f" "$tgt_prefix/$f"
      done
   done
   jq --argjson jpkg "$jpkg" '. += $jpkg' $config > /var/tmp/.pkg.json && \
   cat /var/tmp/.pkg.json > $config && rm -f /var/tmp/.pkg.json
}

Unlink()
{
   local pkg tgt_prefix
   pkg=$1
   tgt_prefix=$(jq -r --arg pkg $pkg '.[$pkg] .tgt' $config)
   
   for it in "include" "lib" "cmake" "pkgconfig"; do
      links="jq -r '.$pkg .$it []' $config"
      for f in $(eval $links); do
         rm -rf "$tgt_prefix/$f"
      done
   done
   jq --arg pkg $pkg 'del (.[$pkg])' $config > "/var/tmp/.pkg.json" && \
   cat "/var/tmp/.pkg.json" > $config && \
   rm -f "/var/tmp/.pkg.json"
}

__pkg_checker__()
{
   local pkg
   pkg=$1
   if [ -z $pkg ]; then
      echo "<pkg> required"
      exit
   fi
   if [ ! -d "$source/$pkg" ]; then 
      echo "[Error] The package \"$pkg\" is not existing!"
      exit
   fi
}

Main()
{
   source="/opt/src"
   target="/opt"
   config="/opt/.pkg.json"
   if [ ! -w $config ]; then
      echo "$config is non-existing or non-writable!"
      # touch $config && chown user:group && echo "{}" >> $config 
      exit
   fi
   cmd=$1
   case $cmd in 
      help | -h | --help |"")
         Help 
         ;;
      -v|--version)
         echo "$SHELL_PROG-$SHELL_VER"
         ;;
      list)
         List
         ;;
      view)
         __pkg_checker__ $2
         View $2
         ;;
      info)
         __pkg_checker__ $2
         Info $2
         ;;
      link)
         __pkg_checker__ $2
         Link $2         ;;
      unlink)
         __pkg_checker__ $2
         Unlink $2
         ;;
      *)
         echo "Not Suppported Command. Please see \`help\` for usage"
         ;;
   esac
}

Main $@
