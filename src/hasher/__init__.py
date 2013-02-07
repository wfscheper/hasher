import importlib

from .parser import md5_parser


def main(argv=None):
    args = md5_parser.parse_args(argv)

    module = importlib.import_module("md5sum.hashes.%s" % args.prog)
    module.run(args)

    """
    def generate(filename):
        if args.binary and not args.text:
            mode = 'rb'
        else:
            mode = 'r'
        with open(filename, mode) as f:
            hexdigest = calculate_md5(f)
        sys.stdout.write('{0}  {1}\n'.format(filename, hexdigest))

    def check(filename):
        '''Check the md5 of file
        '''
        if args.binary or args.text:
            md5_parser.error('the --binary and --text options are '
                                'meaningless when verifying checksums')
        read_errors = 0
        hash_errors = 0
        format_errors = 0

        with open(filename) as f:
            for line in f:
                m = check_re.match(line)
                if not m:
                    format_errors += 1
                    continue
                check_file, binary, md5_hash = m.groups()

                if binary == '*':
                    mode = 'rb'
                else:
                    mode = 'r'

                try:
                    check_f = open(check_file, mode)
                except IOError:
                    sys.stderr.write(
                            'md5sum: {1}: No such file or directory\n'.format(
                                    filename))
                    sys.stdout.write('{0}: FAILED\n'.format(filename))
                    read_errors += 1
                    continue

                if calculate_md5(check_f) == md5_hash:
                    sys.stdout.write('{0}: OK\n'.format(filename))
                else:
                    sys.stdout.write('{0}: FAILED\n'.format(filename))
                    hash_errors += 1
        if format_errors:
            sys.stderr.write('md5sum: WARNING: %s lines are improperly formatted'
                            % format_errors)
        if read_errors:
            sys.stderr.write('md5sum: WARNING: %s listed file could not be read'
                            % read_errors)
        if hash_errors:
            sys.stderr.write('md5sum: WARNING: %s computed checksum did NOT match'
                            % hash_errors)

    if args.check:
        func = check
    else:
        func = generate

    for filename in args.FILE:
        try:
            func(filename)
        except IOError as e:
            sys.stderr.write('md5sum: %s: %s\n' % (filename, e.message))
    """

if __name__ == '__main__':
    main()
