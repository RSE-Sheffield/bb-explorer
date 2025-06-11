<script lang="ts">
	import { getContext } from 'svelte';
	import CitationsModal from './CitationsModal.svelte';
	import Collapsible from '$lib/components/common/Collapsible.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';

	const i18n = getContext('i18n');

	export let id = '';
	export let sources = [];

	let citations = [];
	let showPercentage = false;
	let showRelevance = true;

	let showCitationModal = false;
	let selectedCitation: any = null;
	let isCollapsibleOpen = false;

	function calculateShowRelevance(sources: any[]) {
		const distances = sources.flatMap((citation) => citation.distances ?? []);
		const inRange = distances.filter((d) => d !== undefined && d >= -1 && d <= 1).length;
		const outOfRange = distances.filter((d) => d !== undefined && (d < -1 || d > 1)).length;

		if (distances.length === 0) {
			return false;
		}

		if (
			(inRange === distances.length - 1 && outOfRange === 1) ||
			(outOfRange === distances.length - 1 && inRange === 1)
		) {
			return false;
		}

		return true;
	}

	function shouldShowPercentage(sources: any[]) {
		const distances = sources.flatMap((citation) => citation.distances ?? []);
		return distances.every((d) => d !== undefined && d >= -1 && d <= 1);
	}

	$: {
		console.log('sources', sources);
		citations = sources.reduce((acc, source) => {
			if (Object.keys(source).length === 0) {
				return acc;
			}

			source.document.forEach((document, index) => {
				const metadata = source.metadata?.[index];
				const distance = source.distances?.[index];

				// Within the same citation there could be multiple documents
				const id = metadata?.source ?? source?.source?.id ?? 'N/A';
				let _source = source?.source;

				if (metadata?.name) {
					_source = { ..._source, name: metadata.name };
				}

				if (id.startsWith('http://') || id.startsWith('https://')) {
					_source = { ..._source, name: id, url: id };
				}

				const existingSource = acc.find((item) => item.id === id);
                //console.log(_source);
                // Attempt to detect the subject, volume and chapter
                // "Bibliotheque Britannique: <subject> Vol. <vol>, Chap. <chapter>, Sec. <section> (pp<start>-<end>)"
                if (_source.name != "index.md") {
                    const match = _source.name.match(/bb-([^-]+)-([0-9]{1,2})-([^-]+)-([^-]+)-pg([0-9]{1,3})-([0-9]{1,3})/);
                    if (match) {
                        metadata.subject = match[1].replace(/_/g, " ");
                        metadata.volume = parseInt(match[2])
                        metadata.chapter = match[3].replace(/_/g, " ");
                        metadata.section = match[4].replace(/_/g, " ");
                        metadata.page_start = parseInt(match[5])
                        metadata.page_end = parseInt(match[6])
                        // This acts as the name of the source shown in metadata modal, otherwise it default to filename
                        metadata.name = `Bibliotheque Britannique: ${metadata.subject} Vol. ${metadata.volume}, Chap. ${metadata.chapter}, Sec. ${metadata.section} (pp${metadata.page_start}-${metadata.page_end})`;
                        // Contracted version of the name, to be shown inline with the response
                        // Contracted because if it exceeds ~60 chars the remaining chars are replaced with ellipsis within the UI
                        _source.name = `${metadata.subject} Vol. ${metadata.volume}, Sec. ${metadata.section}`;
                    } else {
                        //metadata.name = "Match failed: "+_source.name
                        console.log(`Source '${_source.name}' does not match`)
                    }
                }
                // Attempt to extract a page number from the body text
                const match = document.match(/\\setcounter\{page\}\{([0-9]+)\}/);
                if (match) {
                    metadata.page = parseInt(match[1]); // Setting page here, displays it next to source in modal
                } else {
                    console.log("Chunk does not contain page num")
                }
                // Append page number to end of URL to take user directly to the page
                const gbooks_dict = {
                  lit_53: "https://books.google.co.uk/books?id=hYdCAAAAcAAJ&hl=en&pg=PA",
                  lit_56: "https://books.google.co.uk/books?id=_Hw1AQAAMAAJ&hl=en&pg=PA",
                  lit_57: "https://books.google.co.uk/books?id=GX01AQAAMAAJ&hl=en&pg=PA",
                  lit_58: "https://books.google.co.uk/books?id=N301AQAAMAAJ&hl=en&pg=PA",
                  lit_59: "https://books.google.co.uk/books?id=RxMPAAAAQAAJ&hl=en&pg=PA",
                  agr_18: "https://books.google.co.uk/books?id=LIlCAAAAcAAJ&hl=en&pg=PA",
                  agr_19: "https://books.google.co.uk/books?id=7-ZEk0HFFEAC&hl=en&pg=PA"
                };
                // Attach a google books URL to metadata if possible to determine it
                const book_code = (metadata.subject.slice(0, 3) + "_" + metadata.volume).toLowerCase();
                if (book_code in gbooks_dict) {
                    if (metadata?.page) {
                        metadata.google_books = gbooks_dict[book_code] + metadata.page;
                    } else {
                        metadata.google_books = gbooks_dict[book_code] + metadata.page_start;
                    }
                }
                
				if (existingSource) {
					existingSource.document.push(document);
					existingSource.metadata.push(metadata);
					if (distance !== undefined) existingSource.distances.push(distance);
				} else {
					acc.push({
						id: id,
						source: _source,
						document: [document],
						metadata: metadata ? [metadata] : [],
						distances: distance !== undefined ? [distance] : undefined
					});
				}
			});
			return acc;
		}, []);
		console.log('citations', citations);

		showRelevance = calculateShowRelevance(citations);
		showPercentage = shouldShowPercentage(citations);
	}

	const decodeString = (str: string) => {
		try {
			return decodeURIComponent(str);
		} catch (e) {
			return str;
		}
	};
</script>

<CitationsModal
	bind:show={showCitationModal}
	citation={selectedCitation}
	{showPercentage}
	{showRelevance}
/>

{#if citations.length > 0}
	<div class=" py-0.5 -mx-0.5 w-full flex gap-1 items-center flex-wrap">
		{#if citations.length <= 3}
			<div class="flex text-xs font-medium flex-wrap">
				{#each citations as citation, idx}
					<button
						id={`source-${id}-${idx + 1}`}
						class="no-toggle outline-hidden flex dark:text-gray-300 p-1 bg-white dark:bg-gray-900 rounded-xl max-w-96"
						on:click={() => {
							showCitationModal = true;
							selectedCitation = citation;
						}}
					>
						{#if citations.every((c) => c.distances !== undefined)}
							<div class="bg-gray-50 dark:bg-gray-800 rounded-full size-4">
								{idx + 1}
							</div>
						{/if}
						<div
							class="flex-1 mx-1 truncate text-black/60 hover:text-black dark:text-white/60 dark:hover:text-white transition"
						>
							{decodeString(citation.source.name)}
						</div>
					</button>
				{/each}
			</div>
		{:else}
			<Collapsible
				id={`collapsible-${id}`}
				bind:open={isCollapsibleOpen}
				className="w-full max-w-full "
				buttonClassName="w-fit max-w-full"
			>
				<div
					class="flex w-full overflow-auto items-center gap-2 text-gray-500 hover:text-gray-600 dark:hover:text-gray-400 transition cursor-pointer"
				>
					<div
						class="flex-1 flex items-center gap-1 overflow-auto scrollbar-none w-full max-w-full"
					>
						<span class="whitespace-nowrap hidden sm:inline shrink-0"
							>{$i18n.t('References from')}</span
						>
						<div class="flex items-center overflow-auto scrollbar-none w-full max-w-full flex-1">
							<div class="flex text-xs font-medium items-center">
								{#each citations.slice(0, 2) as citation, idx}
									<button
										class="no-toggle outline-hidden flex dark:text-gray-300 p-1 bg-gray-50 hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition rounded-xl max-w-96"
										on:click={() => {
											showCitationModal = true;
											selectedCitation = citation;
										}}
										on:pointerup={(e) => {
											e.stopPropagation();
										}}
									>
										{#if citations.every((c) => c.distances !== undefined)}
											<div class="bg-gray-50 dark:bg-gray-800 rounded-full size-4">
												{idx + 1}
											</div>
										{/if}
										<div class="flex-1 mx-1 truncate">
											{decodeString(citation.source.name)}
										</div>
									</button>
								{/each}
							</div>
						</div>
						<div class="flex items-center gap-1 whitespace-nowrap shrink-0">
							<span class="hidden sm:inline">{$i18n.t('and')}</span>
							{citations.length - 2}
							<span>{$i18n.t('more')}</span>
						</div>
					</div>
					<div class="shrink-0">
						{#if isCollapsibleOpen}
							<ChevronUp strokeWidth="3.5" className="size-3.5" />
						{:else}
							<ChevronDown strokeWidth="3.5" className="size-3.5" />
						{/if}
					</div>
				</div>
				<div slot="content">
					<div class="flex text-xs font-medium flex-wrap">
						{#each citations as citation, idx}
							<button
								id={`source-${id}-${idx + 1}`}
								class="no-toggle outline-hidden flex dark:text-gray-300 p-1 bg-gray-50 hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-850 transition rounded-xl max-w-96"
								on:click={() => {
									showCitationModal = true;
									selectedCitation = citation;
								}}
							>
								{#if citations.every((c) => c.distances !== undefined)}
									<div class="bg-gray-50 dark:bg-gray-800 rounded-full size-4">
										{idx + 1}
									</div>
								{/if}
								<div class="flex-1 mx-1 truncate">
									{decodeString(citation.source.name)}
								</div>
							</button>
						{/each}
					</div>
				</div>
			</Collapsible>
		{/if}
	</div>
{/if}
