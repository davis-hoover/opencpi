# This is sourced internally so no error checking
# This script ensures that macports, and the macports versions of gnu utilities, are in the path
case $1 in
    set)
        [ -n "$OCPI_MACOS_SAVED_PATH" ] || export OCPI_MACOS_SAVED_PATH="$PATH"
	[[ "$PATH" =~ (^|:)/opt/local/bin(:|$) ]] || PATH="/opt/local/bin:$PATH"
	[[ "$PATH" =~ (^|:)/opt/local/libexec/gnubin(:|$) ]] || PATH="/opt/local/libexec/gnubin:$PATH"
	;;
    clean)
	[ -z "$OCPI_MACOS_SAVED_PATH" ] || { PATH="$OCPI_MACOS_SAVED_PATH" && unset OCPI_MACOS_SAVED_PATH; }
	;;
esac
