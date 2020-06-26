#!/usr/bin/env python
__doc__ = """Gender Representation in Citations - Circle 
Visualization :: This script uses the output file "Authors.csv" 
that is created by the [1] cleanBib github coding notebook. This
visualization "add-on" will create a circle graph that can aid in 
quickly assessing your bibliography's gender representation as
described in Dworkin et al., 2020 [2] and can be used as an add-on 
to your diversity statement or to visually track your papers' 
citations over time. 
\n
Originally created by Damion V. Demeter
(At OHBM Brainhack June, 17 2020)'
"""
__references__ = """References
----------
[1] Zhou et al., 2020 https://doi.org/10.5281/zenodo.3672109 (https://github.com/dalejn/cleanBib)
[2] Dworkin et al., 2020 https://doi.org/10.1038/s41593-020-0658-y
"""
__version__ = "1.0.0"

import argparse,datetime,logging,os,re,sys,time

from mne.viz import circular_layout, plot_connectivity_circle
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import pandas as pd

pwd = os.getcwd()

def main(argv=sys.argv):
    arg_parser = argparse.ArgumentParser(prog='grepCIRCLE.py',
                                         allow_abbrev=False,
                                         description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         epilog=__references__,
                                         usage='%(prog)s authors_csv [OPTIONS]')
    # Check for arguments. #
    if len(sys.argv[1:])==0:
        print('\nArguments required. Use -h option to print FULL usage.\n')
    arg_parser.add_argument('authors_csv', type=os.path.abspath,
                            help='FULL path to Authors.csv file. (created with cleanBib[1] tool)'
                            )
    arg_parser.add_argument('-ccol', action='store', nargs='*',
                            required=False, default=['indianred','steelblue','mediumpurple','mediumseagreen','aliceblue'],
                            help='Connections color list: '
                                 'Enter 5 SPACE separated matplotlib color names. '
                                 'Req order: MM, MW, WM, WW, Unknown '
                                 '(DEFAULT: [red blue purple green white])',
                            dest='ccol'
                            )
    arg_parser.add_argument('-lcol', action='store', type=str,
                            required=False, default='white',
                            help='Legend background color. Must be matplotlib color string. '
                            '(DEFAULT: white)',
                            dest='lcol'
                            )
    arg_parser.add_argument('-ncol', action='store', nargs='*',
                            required=False, default=['dimgrey','tab:red','tab:blue','tab:purple','tab:green','white'],
                            help='Node color list: '
                                 'Enter 6 SPACE separated matplotlib color names. '
                                 'Req order: labels, MM, MW, WM, WW, Unknown '
                                 '(DEFAULT: [dimgrey red blue purple green white])',
                            dest='ncol'
                            )
    arg_parser.add_argument('-o', action='store', type=os.path.abspath, 
                            required=False, default=pwd,
                            help='Location for saved circle graph image. (DEFAULT: pwd)',
                            dest='out_dir'
                            )
    arg_parser.add_argument('-t', action='store', type=str,
                            nargs='+', required=False,
                            help='Title for circle graph. (DEFAULT: None)',
                            default=None,
                            dest='title'
                            )
    arg_parser.add_argument('-q', action='store_true', required=False,
                            help='Quiet mode suppresses all QA/extra info '
                                 'printouts. (Errors always printed)',
                            dest='quiet'
                            )
    arg_parser.add_argument('-v','--version', action='version', version='%(prog)s: ' + __version__)
    args = arg_parser.parse_args()
    # Setting up logger #
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    logger = logging.getLogger()
    logging.getLogger('matplotlib.font_manager').disabled = True
    if not args.quiet:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.ERROR)

    #################################################
    ## Script Argument Verification and Assignment ##
    #################################################
    logger.debug('\n--------------------- setup info ---------------------------------')
    # Verify Authors.csv file/path
    if os.path.isfile(args.authors_csv):
        logger.debug(f'-Authors.csv verified: {os.path.abspath(args.authors_csv)}')
    else:
        sys.exit('\nERROR: Authors.csv does not exist. Please verify path. Exiting...\n')
    # Verify connection color list length
    if len(args.ccol) == 5:
        ccol = args.ccol
        logger.debug(f'-Connection color list: {ccol}')
    else:
        sys.exit('\nERROR: User defined connection color list is an incorrect length. Please check. Exiting...\n')
    # Verify node color list length
    if len(args.ncol) == 6:
        ncol = args.ncol
        logger.debug(f'-Node color list: {ncol}')
    else:
        sys.exit('\nERROR: User defined node color list is an incorrect length. Please check. Exiting...\n')
    # Verify and format title
    if args.title:
        title = ' '.join(args.title)
        png_name = '_'.join(args.title + ['Citation','Circle'])
        png_name = re.sub(r'\W+', '', png_name)
    else:
        title = ''
        png_name = 'Gender_Rep_Citation_Circle_Figure'
    logger.debug(f'-Title: {title}')
    # Verify output path
    if os.path.isdir(args.out_dir):
        logger.debug(f'-Out path: {os.path.join(args.out_dir,png_name)}')
    else:
        sys.exit('\nERROR: Output path not valid. Please verify path. Exiting...\n')
    logger.debug('--------------------------- end ---------------------------------\n')
    #################################################
    ##          Global Variable Assignment         ##
    #################################################
    start_time=time.time()
    time.sleep(1)
    today_date = datetime.datetime.now().strftime('%m%d%Y')

    # Global Label info
    type_labels = ['Spacer1','Man - Man','Man - Woman','Woman - Man','Woman - Woman','Unknown','Spacer2']

    #################################################
    ##               DEFINE FUNCTIONS              ##
    #################################################
    def make_mat(authors_df):
        ## Parse citation type and Create label names for graph
        # first group into citation type ()
        MM = authors_df.loc[authors_df['GendCat'] == 'MM', 'CitationKey'].tolist()
        MW = authors_df.loc[authors_df['GendCat'] == 'MW', 'CitationKey'].tolist()
        WM = authors_df.loc[authors_df['GendCat'] == 'WM', 'CitationKey'].tolist()
        WW = authors_df.loc[authors_df['GendCat'] == 'WW', 'CitationKey'].tolist()
        U = authors_df.loc[authors_df['GendCat'].str.contains(r'U'), 'CitationKey'].tolist()

        # arrange labels in CORRECT/MATRIX order (this must match the matrix axis order)
        papers_label_list = MM + MW + WM + WW + U
        # Now append label names for full matrix order list
        label_names = type_labels + papers_label_list

        logger.debug(f'\n-Matrix order label names: {label_names}\n')

        # Label indices (hardcorded for now) for index reference 
        mat_list = []

        for lab in label_names:
            temp_list = [0] * len(label_names)
            if lab in MM:
                temp_list[1] = 1
            elif lab in MW:
                temp_list[2] = 2
            elif lab in WM:
                temp_list[3] = 3
            elif lab in WW:
                temp_list[4] = 4
            elif lab in U:
                temp_list[5] = 5
            mat_list.append(temp_list)

        cite_mat = np.asarray(mat_list)
        logger.debug(f'Number of citations found: {cite_mat.shape[0]}')

        return cite_mat, papers_label_list, label_names

    def make_circle(authors_df, label_names):
        ## Prep all labels, colors, etc 
        # Create node colors
        types_colors = [ncol[0]] * len(type_labels)
        mm_colors = [ncol[1]] * len(authors_df.loc[authors_df['GendCat'] == 'MM', 'CitationKey'])
        mw_colors = [ncol[2]] * len(authors_df.loc[authors_df['GendCat'] == 'MW', 'CitationKey'])
        wm_colors = [ncol[3]] * len(authors_df.loc[authors_df['GendCat'] == 'WM', 'CitationKey'])
        ww_colors = [ncol[4]] * len(authors_df.loc[authors_df['GendCat'] == 'WW', 'CitationKey'])
        u_colors = [ncol[5]] * len(authors_df.loc[authors_df['GendCat'].str.contains(r'U'), 'CitationKey'])

        # LABEL COLORS GO IN THE ORIGINAL/MATRIX ORDER , not the reordered order!
        label_colors = types_colors + mm_colors + mw_colors + wm_colors + ww_colors + u_colors

        # MAKE NODE ORDER TO MAKE THE CIRCLE LOOK NICER - Node order is ONLY on the circle, not the matrix order. 
        pre_labels = ['Man - Man','Man - Woman','Spacer1']
        post_labels = ['Spacer2','Woman - Man','Woman - Woman','Unknown']

        # This node order is for the graph only! (ordered from starting point counter clockwise)
        node_order = pre_labels + papers_label_list + post_labels
        # now clean node order remove spacer labels only for graphing (angles needs all to be unique and match matrix)
        cleaned_label_names = [' ' if 'Spacer' in i else i for i in label_names]

        # Optional(?) clean paper titles for better looking graph
        cleaned_titles = []
        for paper in cleaned_label_names:
            x = re.split('(\d+)',paper)
            if len(x) == 3:
                cleaned_titles.append(f'{x[0]} ({x[1]})')
            else:
                cleaned_titles.append(paper)
         
        logger.debug(f'\n-Cleaned titles list: {cleaned_titles}\n')

        ## PREP FIGURE ##
        fig = plt.figure(figsize=(30, 30), facecolor='black')

        ## MAKE NODES ANGLES ##
        sp = 90
        node_angles = circular_layout(label_names, node_order, start_pos=sp)

        ## Make custom colormap (if used)
        cmap = colors.ListedColormap(['black',
                                      ccol[0],ccol[1],
                                      ccol[2],ccol[3],
                                      ccol[4]])
        boundaries = [0, 1, 2, 3, 4, 5]
        norm = colors.BoundaryNorm(boundaries, cmap.N, clip=True)

        # Make Custom/Manual Legend
        MM_patch = mpatches.Patch(facecolor=ncol[1], label='Man / Man', linewidth = 1, edgecolor = 'black')
        MW_patch = mpatches.Patch(facecolor=ncol[2], label='Man / Woman', linewidth = 1, edgecolor = 'black')
        WM_patch = mpatches.Patch(facecolor=ncol[3], label='Woman / Man', linewidth = 1, edgecolor = 'black')
        WW_patch = mpatches.Patch(facecolor=ncol[4], label='Woman / Woman', linewidth = 1, edgecolor = 'black')
        U_patch = mpatches.Patch(facecolor=ncol[5], label='Unknown', linewidth = 1, edgecolor = 'black')
        legend = plt.gcf().legend(handles=[MM_patch,MW_patch,WM_patch,WW_patch,U_patch],
                         loc=1, facecolor=args.lcol, framealpha=.98, prop={'size':35},
                         fancybox=True, title='Citation Type',title_fontsize=40)

        # change legen color text?
        # plt.setp(legend.get_texts(), color='g')

        ## Create Circle Graph
        plot_connectivity_circle(cite_mat, cleaned_titles,
                                 node_angles=node_angles,
                                 node_colors=label_colors,
                                 title=title, padding=4, fontsize_title=48,
                                 textcolor='white', facecolor='black',
                                 colormap=cmap, colorbar=False, fig=fig,
                                 linewidth=4, fontsize_names=25,
                                 subplot=111,
                                 interactive=False, show=False
                                )

        ## SAVE FIGURE ##
        out_fig = os.path.abspath(os.path.join(args.out_dir,png_name))

        # have to re-set the facecolor before saving #
        fig.savefig(out_fig, facecolor='black')

    #################################################
    ##               MAIN SCRIPT ENTRY             ##
    #################################################
    # I. Read csv to df
    authors_df = pd.read_csv(args.authors_csv)
    # II. Create "fake" conn matrix
    cite_mat, papers_label_list, label_names = make_mat(authors_df)
    # III. Create/format labels and make figure 
    make_circle(authors_df, label_names)

    full_runtime = time.time() - start_time
    print('\nFull Script Runtime: ' + str(datetime.timedelta(seconds=round(full_runtime))) + '\n')

if __name__ == '__main__':
    sys.exit(main())